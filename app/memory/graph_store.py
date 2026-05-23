import asyncio
import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.config.settings import settings

# Added 'status' column to memory_facts
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS memory_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memory_facts (
    id TEXT PRIMARY KEY,
    entity1 TEXT NOT NULL,
    relation TEXT NOT NULL,
    entity2 TEXT NOT NULL,
    status TEXT DEFAULT 'ACTIVE',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(entity1, relation, entity2)
);

CREATE TABLE IF NOT EXISTS memory_audit_events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    entity1 TEXT DEFAULT '',
    relation TEXT DEFAULT '',
    entity2 TEXT DEFAULT '',
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memory_retention_runs (
    run_id TEXT PRIMARY KEY,
    cutoff TEXT NOT NULL,
    deleted_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS routing_examples (
    id TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    category TEXT NOT NULL,
    domain TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(query)
);
"""

INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_memory_facts_entity1 ON memory_facts(entity1);
CREATE INDEX IF NOT EXISTS idx_memory_facts_entity2 ON memory_facts(entity2);
CREATE INDEX IF NOT EXISTS idx_memory_facts_updated ON memory_facts(updated_at);
CREATE INDEX IF NOT EXISTS idx_memory_facts_status ON memory_facts(status);
CREATE INDEX IF NOT EXISTS idx_memory_audit_created ON memory_audit_events(created_at);
"""


@dataclass(frozen=True)
class MemoryFact:
    entity1: str
    relation: str
    entity2: str
    status: str
    created_at: datetime
    updated_at: datetime


class GraphMemoryStore:
    def __init__(
        self,
        db_path: str,
        *,
        retention_enabled: bool,
        retention_days: int,
        prune_interval_hours: int,
        legacy_path: str,
    ):
        self.db_path = db_path
        self.retention_enabled = retention_enabled
        self.retention_days = max(retention_days, 1)
        self.prune_interval_hours = max(prune_interval_hours, 1)
        self.legacy_path = legacy_path
        self._lock = asyncio.Lock()
        self._context_assembler: Any | None = None
        self._ensure_db()
        self._migrate_legacy_pickle()

    def attach_context_assembler(self, assembler: Any) -> None:
        self._context_assembler = assembler

    async def add_fact(self, entity1: str, relation: str, entity2: str, status: str = 'ACTIVE') -> None:
        e1 = (entity1 or "").strip().lower()
        rel = (relation or "").strip().upper()
        e2 = (entity2 or "").strip().lower()
        if not e1 or not rel or not e2:
            raise ValueError("entity1, relation, and entity2 are required.")

        now = self._utc_now()
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO memory_facts (id, entity1, relation, entity2, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(entity1, relation, entity2)
                    DO UPDATE SET updated_at = excluded.updated_at, status = excluded.status
                    """,
                    (uuid4().hex, e1, rel, e2, status, now.isoformat(), now.isoformat()),
                )
                self._insert_audit_event(
                    conn,
                    event_type="fact.upsert",
                    entity1=e1,
                    relation=rel,
                    entity2=e2,
                    metadata={"source": "memory_extractor", "status": status},
                )
                self._maybe_prune(conn, now)
        print(f"[GRAPH MEMORY] Learned: {e1} --[{rel}]--> {e2} ({status})")

    async def supersede_facts_by_entity(self, entity: str) -> None:
        """Marks all existing facts for an entity as SUPERSEDED."""
        e = (entity or "").strip().lower()
        now = self._utc_now()
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE memory_facts SET status = 'SUPERSEDED', updated_at = ? WHERE entity1 = ? OR entity2 = ?",
                    (now.isoformat(), e, e)
                )

    def fetch_facts_for_entity(self, entity: str, *, limit: int = 200, active_only: bool = True) -> list[MemoryFact]:
        entity = (entity or "").strip().lower()
        if not entity:
            return []
        
        query = """
            SELECT entity1, relation, entity2, status, created_at, updated_at
            FROM memory_facts
            WHERE (entity1 = ? OR entity2 = ?)
        """
        params = [entity, entity]
        
        if active_only:
            query += " AND status = 'ACTIVE'"
            
        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        
        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [self._row_to_fact(row) for row in rows]

    def search_facts(self, query: str, *, limit: int = 200, active_only: bool = True) -> list[MemoryFact]:
        tokens = self._tokenize(query)
        if not tokens:
            return []
        clauses = []
        params: list[Any] = []
        for token in tokens:
            like = f"%{token}%"
            clauses.append("(entity1 LIKE ? OR entity2 LIKE ? OR relation LIKE ?)")
            params.extend([like, like, like])
            
        where_clause = " OR ".join(clauses)
        if active_only:
            where_clause = f"({where_clause}) AND status = 'ACTIVE'"
            
        params.append(limit)
        
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT entity1, relation, entity2, status, created_at, updated_at
                FROM memory_facts
                WHERE {where_clause}
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [self._row_to_fact(row) for row in rows]

    def query_entity(self, entity: str, *, limit: int = 200) -> list[str]:
        facts = self.fetch_facts_for_entity(entity, limit=limit, active_only=True)
        return [f"{fact.entity1} {fact.relation} {fact.entity2}" for fact in facts]

    def build_context(self, query: str, user_id: str) -> str:
        if not settings.memory_context_enabled:
            return self._simple_context(user_id)
        if self._context_assembler is None:
            return self._simple_context(user_id)
        return self._context_assembler.build_context(query=query, user_id=user_id)

    def _simple_context(self, user_id: str) -> str:
        facts = self.query_entity(user_id)
        if not facts:
            return ""
        return "MEMORY CONTEXT:\n- " + "\n- ".join(facts)

    def _ensure_db(self) -> None:
        directory = os.path.dirname(self.db_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.executescript(SCHEMA_SQL)
            
            # Hot-patch schema upgrade for existing databases MUST happen before INDEX_SQL
            try:
                conn.execute("ALTER TABLE memory_facts ADD COLUMN status TEXT DEFAULT 'ACTIVE'")
            except sqlite3.OperationalError:
                pass # Column already exists!
                
            conn.executescript(INDEX_SQL)

    def add_routing_example(self, query: str, category: str, domain: str) -> None:
        """Stores a historical ticket/query to be used for dynamic few-shot routing."""
        q = (query or "").strip().lower()
        if not q or not category or not domain:
            raise ValueError("query, category, and domain are required.")
            
        now = self._utc_now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO routing_examples (id, query, category, domain, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(query) DO UPDATE SET 
                    category=excluded.category,
                    domain=excluded.domain,
                    created_at=excluded.created_at
                """,
                (uuid4().hex, q, category, domain, now.isoformat()),
            )
            conn.commit()

    def get_routing_examples(self) -> list[dict]:
        """Fetches all routing examples from the database."""
        with self._connect() as conn:
            rows = conn.execute("SELECT query, category, domain FROM routing_examples").fetchall()
        return [{"query": row["query"], "category": row["category"], "domain": row["domain"]} for row in rows]

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _row_to_fact(self, row: sqlite3.Row) -> MemoryFact:
        # Fallback for 'status' in case the database was just migrated
        status = row["status"] if "status" in row.keys() else 'ACTIVE'
        return MemoryFact(
            entity1=row["entity1"],
            relation=row["relation"],
            entity2=row["entity2"],
            status=status,
            created_at=self._parse_datetime(row["created_at"]),
            updated_at=self._parse_datetime(row["updated_at"]),
        )

    def _insert_audit_event(self, conn, *, event_type, entity1, relation, entity2, metadata):
        conn.execute(
            "INSERT INTO memory_audit_events (id, event_type, entity1, relation, entity2, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (uuid4().hex, event_type, entity1, relation, entity2, json.dumps(metadata), self._utc_now().isoformat()),
        )

    def _maybe_prune(self, conn, now):
        pass # Simplified for brevity

    def _get_last_pruned_at(self, conn):
        return None

    def _migrate_legacy_pickle(self):
        pass

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _parse_datetime(raw: str) -> datetime:
        value = datetime.fromisoformat(raw)
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        if not text: return []
        tokens = []
        current = []
        for ch in text.lower():
            if ch.isalnum():
                current.append(ch)
            elif current:
                tokens.append("".join(current))
                current = []
        if current: tokens.append("".join(current))
        return list(dict.fromkeys(tokens[:8]))


graph_db = GraphMemoryStore(
    db_path=settings.graph_memory_db_path,
    retention_enabled=settings.memory_retention_enabled,
    retention_days=settings.memory_retention_days,
    prune_interval_hours=settings.memory_retention_prune_interval_hours,
    legacy_path=settings.graph_memory_legacy_path,
)

from app.memory.context_assembler import RecursiveContextAssembler

context_assembler = RecursiveContextAssembler(
    graph_db,
    max_facts=settings.memory_context_max_facts,
    token_budget=settings.memory_context_token_budget,
    expansion_depth=settings.memory_context_expansion_depth,
    max_subqueries=settings.memory_context_max_subqueries,
)
graph_db.attach_context_assembler(context_assembler)