import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

# --- WAGGLE-INSPIRED EDGE ---
# We reuse the BGE-Reranker from retriever.py to semantically score graph connections!
import numpy as np
# ----------------------------

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "the", "and", "or", "for", "with", "this", "that", "what", "when", 
    "where", "which", "how", "who", "from", "into", "about", "your", 
    "their", "have", "has", "had", "user", "issue", "problem", "help",
}

@dataclass
class Subquery:
    query: str
    purpose: str
    weight: float

# Removed frozen=True so we can dynamically update the semantic score
@dataclass
class Candidate:
    entity1: str
    relation: str
    entity2: str
    updated_at: datetime
    score: float


class RecursiveContextAssembler:
    def __init__(
        self,
        store: Any,
        *,
        max_facts: int,
        token_budget: int,
        expansion_depth: int,
        max_subqueries: int,
    ) -> None:
        self.store = store
        self.max_facts = max_facts
        self.token_budget = token_budget
        self.expansion_depth = max(expansion_depth, 0)
        self.max_subqueries = max(max_subqueries, 1)

    def build_context(self, query: str, user_id: str) -> str:
        normalized_query = (query or "").strip()
        normalized_user = (user_id or "").strip().lower()
        subqueries = self._decompose(normalized_query, normalized_user)

        candidates: dict[tuple[str, str, str], Candidate] = {}

        # 1. Fetch User Entrypoints
        if normalized_user:
            for fact in self.store.fetch_facts_for_entity(normalized_user, limit=self.max_facts * 3):
                candidate = self._candidate_from_fact(fact, tokens=set(), user_id=normalized_user, weight=0.8)
                self._upsert_candidate(candidates, candidate)

        # 2. Fetch Query Entrypoints
        for subquery in subqueries:
            facts = self.store.search_facts(subquery.query, limit=self.max_facts * 5)
            tokens = set(self._tokenize(subquery.query))
            for fact in facts:
                candidate = self._candidate_from_fact(
                    fact,
                    tokens=tokens,
                    user_id=normalized_user,
                    weight=subquery.weight,
                )
                self._upsert_candidate(candidates, candidate)

        if not candidates:
            return ""

        # 3. Graph Expansion (Traverse connections)
        expanded = self._expand_candidates(candidates.values())
        for candidate in expanded:
            self._upsert_candidate(candidates, candidate)

        # 4. CROSS-ENCODER GRAPH RERANKING
        # Instead of just keyword matching, we semantically rank the graph paths!
        from app.rag.retriever import reranker
        
        # CRITICAL FIX: Cap the number of semantic reranking candidates to 50 to prevent Timeouts!
        candidate_list = list(candidates.values())[:50]
        pairs = [[normalized_query, f"{c.entity1} {c.relation} {c.entity2}"] for c in candidate_list]
        
        try:
            raw_scores = reranker.predict(pairs)
            probabilities = 1 / (1 + np.exp(-raw_scores))
            
            print("\n--- GRAPH SEMANTIC SCORES ---")
            for idx, c in enumerate(candidate_list):
                semantic_score = probabilities[idx]
                recency_bonus = self._recency_boost(c.updated_at) * 0.15
                c.score = float(semantic_score + recency_bonus)
                
                if semantic_score > 0.4:
                    print(f"Graph Fact: {c.entity1} {c.relation} {c.entity2} | Score: {c.score:.4f}")
            print("-----------------------------\n")
            
        except Exception as e:
            print(f"[GRAPH RERANKING ERROR] {e}")

        # 5. Compress and Return
        ranked = sorted(candidate_list, key=lambda item: (item.score, item.updated_at), reverse=True)
        lines = self._compress(ranked)
        if not lines:
            return ""
        return "MEMORY CONTEXT:\n- " + "\n- ".join(lines)

    def _decompose(self, query: str, user_id: str) -> list[Subquery]:
        if not query and user_id:
            return [Subquery(query=user_id, purpose="user_facts", weight=0.9)]
        tokens = self._tokenize(query)
        topic = " ".join(tokens[:4]) if tokens else query
        templates = [
            Subquery(query=query, purpose="original", weight=1.0),
            Subquery(query=f"{topic} recent issue", purpose="recent_issue", weight=0.9),
            Subquery(query=f"{topic} device", purpose="device_context", weight=0.8),
        ]
        if user_id:
            templates.append(Subquery(query=user_id, purpose="user_facts", weight=0.8))
        return templates[: self.max_subqueries]

    def _candidate_from_fact(self, fact: Any, *, tokens: set[str], user_id: str, weight: float) -> Candidate:
        text = f"{fact.entity1} {fact.relation} {fact.entity2}".lower()
        match_ratio = self._match_ratio(text, tokens)
        score = match_ratio * weight
        if user_id and (fact.entity1 == user_id or fact.entity2 == user_id):
            score += 0.2
        return Candidate(
            entity1=fact.entity1,
            relation=fact.relation,
            entity2=fact.entity2,
            updated_at=fact.updated_at,
            score=score,
        )

    def _expand_candidates(self, candidates: Iterable[Candidate]) -> list[Candidate]:
        if self.expansion_depth <= 0: return []
        seeds = sorted(candidates, key=lambda item: item.score, reverse=True)[:3]
        expanded: list[Candidate] = []
        for seed in seeds:
            entities = {seed.entity1, seed.entity2}
            for entity in entities:
                for fact in self.store.fetch_facts_for_entity(entity, limit=self.max_facts * 2):
                    expanded.append(
                        Candidate(
                            entity1=fact.entity1, relation=fact.relation, entity2=fact.entity2,
                            updated_at=fact.updated_at, score=0.1
                        )
                    )
        return expanded

    def _compress(self, ranked: list[Candidate]) -> list[str]:
        char_budget = max(self.token_budget * 4, 200)
        lines: list[str] = []
        used = 0
        seen: set[tuple[str, str, str]] = set()
        
        for item in ranked:
            # Drop low semantic scores automatically
            if item.score < 0.2: 
                continue
                
            key = (item.entity1, item.relation, item.entity2)
            if key in seen:
                continue
            line = f"{item.entity1} {item.relation} {item.entity2}"
            if used + len(line) > char_budget:
                break
            lines.append(line)
            used += len(line)
            seen.add(key)
            if len(lines) >= self.max_facts:
                break
        return lines

    @staticmethod
    def _match_ratio(text: str, tokens: set[str]) -> float:
        if not tokens: return 0.0
        matches = sum(1 for token in tokens if token in text)
        return matches / max(len(tokens), 1)

    @staticmethod
    def _recency_boost(updated_at: datetime) -> float:
        now = datetime.now(timezone.utc)
        age_days = max((now - updated_at).total_seconds() / 86400.0, 0.0)
        return math.exp(-age_days / 30.0)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        tokens = []
        for token in _TOKEN_RE.findall(text.lower()):
            if token in _STOPWORDS or len(token) <= 2: continue
            tokens.append(token)
        return tokens

    @staticmethod
    def _upsert_candidate(candidates: dict[tuple[str, str, str], Candidate], candidate: Candidate) -> None:
        key = (candidate.entity1, candidate.relation, candidate.entity2)
        existing = candidates.get(key)
        if existing is None or candidate.score > existing.score:
            candidates[key] = candidate