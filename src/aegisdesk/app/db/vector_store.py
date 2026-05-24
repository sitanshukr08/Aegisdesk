import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

from aegisdesk.app.config.settings import settings

embeddings = FastEmbedEmbeddings(model_name=settings.embed_model)

def get_embeds():
    return embeddings

_global_chroma_db = None

def get_db():
    global _global_chroma_db
    if _global_chroma_db is None:
        client = chromadb.PersistentClient(
            path=settings.db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        _global_chroma_db = Chroma(
            client=client,
            collection_name="hcltech_knowledge_base",
            embedding_function=embeddings
        )
    return _global_chroma_db

_global_cache_db = None

def get_cache_db():
    global _global_cache_db
    if _global_cache_db is None:
        client = chromadb.PersistentClient(
            path=settings.db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        _global_cache_db = Chroma(
            client=client,
            collection_name="semantic_cache",
            embedding_function=embeddings
        )
    return _global_cache_db
