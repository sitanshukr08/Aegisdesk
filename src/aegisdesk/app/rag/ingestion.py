import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import Chroma

from aegisdesk.app.config.settings import settings
from aegisdesk.app.db.vector_store import get_embeds


def process_uploaded_file(file_path: str, filename: str) -> bool:
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

        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_documents(docs)

        client = chromadb.PersistentClient(path=settings.db_path)
        embeds = get_embeds()
        
        # Save documents explicitly with cosine space
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
