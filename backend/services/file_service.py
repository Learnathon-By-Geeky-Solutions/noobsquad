# services/file_service.py
import os
from fastapi import HTTPException
from fastapi.responses import FileResponse
from services.FileHandler import validate_file_extension, generate_secure_filename, save_upload_file
from werkzeug.utils import secure_filename
from pathlib import Path
from dotenv import load_dotenv
from utils.supabase import upload_file_to_supabase
import uuid
from fastapi.responses import StreamingResponse

load_dotenv()
UPLOAD_DIR = Path("uploads/research_papers")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
API_URL = os.getenv("VITE_API_URL")
ALLOWED_DOCS = [".pdf", ".doc", ".docx"]

async def save_uploaded_research_paper(file, user_id: int) -> str:
    ext = validate_file_extension(file.filename, ALLOWED_DOCS)
    filename = secure_filename(generate_secure_filename(user_id, ext))
    file_path = await upload_file_to_supabase(file, filename, section="research_papers")
    return file_path

def get_file_response(filepath: str, filename: str):
    validate_file_existence(filepath)
    return FileResponse(path=filepath, filename=filename, media_type="application/pdf")
