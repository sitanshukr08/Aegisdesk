import json
import hashlib
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from src.aegisdesk.core.pipeline import execute_rag_pipeline
from app.services.vision_service import analyze_screenshot
from app.memory.extractor import extract_memory_background 

# --- SECURITY IMPORTS ---
from app.services.auth_service import get_current_user, require_admin, TokenData
# ------------------------

from cachetools import TTLCache
router = APIRouter()
# Prevent memory leak by caching maximum 1000 sessions for 10 minutes each
RESPONSE_CACHE = TTLCache(maxsize=1000, ttl=600)

class QueryRequest(BaseModel):
    query: str
    session_id: str
    user_approval: Optional[bool] = None

def get_cache_key(query: str, username: str) -> str:
    return hashlib.md5(f"{username}:{query}".lower().strip().encode('utf-8')).hexdigest()

@router.post("/query")
async def query_bot(
    request: QueryRequest, 
    background_tasks: BackgroundTasks,
    current_user: TokenData = Depends(get_current_user) # Secure!
):
    try:
        user_id = current_user.username
        cache_key = get_cache_key(request.query, user_id)
        
        if cache_key in RESPONSE_CACHE:
            print(f"[CACHE HIT] Serving instantly for: {request.query}")
            async def cache_generator():
                for chunk in RESPONSE_CACHE[cache_key]:
                    yield chunk
            return StreamingResponse(cache_generator(), media_type="text/event-stream")

        background_tasks.add_task(extract_memory_background, user_id, request.query)

        async def event_generator():
            full_response_chunks = []
            async for stream_block in execute_rag_pipeline(request.query, user_id, request.session_id, user_approval=request.user_approval):
                chunk_str = f"data: {json.dumps(stream_block)}\n\n"
                full_response_chunks.append(chunk_str)
                yield chunk_str
            RESPONSE_CACHE[cache_key] = full_response_chunks
            
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest")
async def ingest_document(
    file: UploadFile = File(...),
    current_user: TokenData = Depends(require_admin) # Secure! Only Admins!
):
    try:
        from app.db.vector_store import get_db
        from langchain_core.documents import Document
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        
        content = await file.read()
        text = content.decode("utf-8")
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(text)
        docs = [Document(page_content=chunk, metadata={"source": file.filename}) for chunk in chunks]
        
        db = get_db()
        db.add_documents(docs)
        
        global RESPONSE_CACHE
        RESPONSE_CACHE.clear()
        
        return {"message": f"Successfully ingested {len(chunks)} chunks.", "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "HCLTech AI AegisDesk API - Secured"}