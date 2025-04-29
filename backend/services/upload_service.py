# services/upload_service.py

from fastapi import UploadFile, HTTPException
from pathlib import Path
from utils.cloudinary import upload_to_cloudinary

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".docx"}

async def validate_and_upload(file: UploadFile):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    return await upload_to_cloudinary(file)
