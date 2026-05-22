from app.db.vector_store import get_db
from app.config.settings import settings
from fastembed.rerank.cross_encoder import TextCrossEncoder
import numpy as np
from app.memory.graph_store import graph_db
from src.aegisdesk.observability.logger import get_logger
import asyncio

logger = get_logger("aegisdesk.retriever")

reranker = TextCrossEncoder(model_name='BAAI/bge-reranker-base')

async def get_context(user_id: str, original_q: str, expanded_q: str):
    try:
        user_memory = ""
        memory_context = graph_db.build_context(original_q, user_id)
        if memory_context:
            user_memory = f"{memory_context}\n\n"
            logger.debug(f"Injected memory context for {user_id}!")
            
        db = get_db()
        
        res_orig = db.similarity_search(original_q, k=10)
        res_exp = db.similarity_search(expanded_q, k=10)
        
        unique_docs = {doc.page_content: doc for doc in (res_orig + res_exp)}.values()
        unique_texts = [doc.page_content for doc in unique_docs]
        
        if not unique_texts:
            if user_memory:
                return user_memory, 0.90
            return "", 0.0
            
        # CRITICAL FIX: Offload heavy ONNX inference to a worker thread!
        raw_scores = await asyncio.to_thread(lambda: list(reranker.rerank(expanded_q, unique_texts)))
        
        probabilities = 1 / (1 + np.exp(-np.array(raw_scores)))
        
        scored_docs = list(zip(unique_texts, probabilities))
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        final_texts = []
        final_scores = []
        
        logger.debug("--- BGE-RERANKER PROBABILITIES ---")
        for text, score in scored_docs:
            logger.debug(f"Snippet: {text[:30]}... | Prob: {score:.4f}")
            if score > 0.30:
                final_texts.append(text)
                final_scores.append(score)
            
            if len(final_texts) >= settings.top_k:
                break
        logger.debug("----------------------------------")
        
        if not final_texts:
            if user_memory:
                return user_memory, 0.90
            return "", 0.0 

        context = user_memory + "KNOWLEDGE BASE DOCUMENTS:\n" + "\n---\n".join(final_texts)
        avg_score = sum(final_scores) / len(final_scores)
        
        return context, avg_score
        
    except Exception as e:
        logger.error(f"Retriever error: {e}", exc_info=True)
        return "", 0.0
