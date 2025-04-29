# services/upload_service.py

from fastapi import UploadFile, HTTPException
from pathlib import Path
from utils.supabase import upload_file_to_supabase
from services.FileHandler import generate_secure_filename
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf"}

async def validate_and_upload(file: UploadFile):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    filename = generate_secure_filename(file.filename, ext)
    return await upload_file_to_supabase(file, filename, section="chat")

