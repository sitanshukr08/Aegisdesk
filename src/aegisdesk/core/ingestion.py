"""
Core Ingestion Logic.
Handles reading files, chunking text, and embedding them into ChromaDB.
"""

import chromadb
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config.settings import settings
from app.db.vector_store import get_embeds


def process_file_to_chroma(file_path: str, filename: str) -> bool:
    """Reads a file, chunks it, and saves embeddings into ChromaDB."""
    try:
        docs = []
        if filename.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
            docs.extend(loader.load())
        elif filename.endswith(".txt"):
            loader = TextLoader(file_path)
            docs.extend(loader.load())
        else:
            return False

        if not docs:
            return False

        # Split documents into smaller semantic chunks
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_documents(docs)

        # Connect to ChromaDB
        client = chromadb.PersistentClient(path=settings.db_path)
        embeds = get_embeds()
        
        # Save documents explicitly with cosine space for better semantic matching
        Chroma.from_documents(
            documents=chunks,
            embedding=embeds,
            client=client,
            collection_name="it_support_kb",
            collection_metadata={"hnsw:space": "cosine"}
        )
        return True
    except Exception as e:
        print(f"Ingestion error: {e}")
        return False