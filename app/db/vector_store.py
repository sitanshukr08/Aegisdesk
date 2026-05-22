from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import chromadb
from chromadb.config import Settings
from app.config.settings import settings

embeddings = HuggingFaceEmbeddings(model_name=settings.embed_model)

def get_embeds():
    return embeddings

_global_chroma_db = None

def get_db():
    global _global_chroma_db
    if _global_chroma_db is None:
        client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(anonymized_telemetry=False)
        )
        _global_chroma_db = Chroma(
            client=client,
            collection_name="hcltech_knowledge_base",
            embedding_function=embeddings
        )
    return _global_chroma_db
