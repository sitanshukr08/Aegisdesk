import os

from fastapi import APIRouter, File, HTTPException, UploadFile

from aegisdesk.app.models.schemas import QueryReq, QueryRes
from aegisdesk.app.rag.ingestion import process_uploaded_file
from aegisdesk.app.services.chat_service import process_user_query

router = APIRouter()

@router.post("/query", response_model=QueryRes)
async def handle_query(req: QueryReq):
    try:
        res = await process_user_query(req.session_id, req.query)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    os.makedirs("./data", exist_ok=True)
    
    file_path = f"./data/{file.filename}"
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
        
    success = process_uploaded_file(file_path, file.filename)
    
    if not success:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail="Failed to process file. Ensure it is a valid TXT or PDF.")
        
    return {"message": f"Successfully ingested {file.filename} into ChromaDB"}
