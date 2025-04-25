import logging
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from models.research_paper import ResearchPaper
from core.dependencies import get_db
from api.v1.endpoints.Auth.auth import get_current_user  # Ensure authentication middleware is implemented
from models.user import User
from werkzeug.utils import secure_filename
from pathlib import Path
from datetime import datetime, timezone
from services.services import  save_upload_file, validate_file_extension, generate_secure_filename

router = APIRouter()

give_error = "Internal Server Error"
# Directory for storing research papers
UPLOAD_DIR = Path("uploads/research_papers")  # ✅ Ensure UPLOAD_DIR is a Path object
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)  # ✅ Create directory if it doesn't exist
ALLOWED_DOCS = [".pdf", ".doc", ".docx"]

@router.post("/upload-paper/")
async def upload_paper(
    title: str = Form(...),
    author: str = Form(...),
    research_field: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a research paper (PDF/DOC) with metadata.
    Stores file with secure filename and only keeps filename in DB.
    """
    try:
        # ✅ Validate extension
        ext = validate_file_extension(file.filename, ALLOWED_DOCS)

        # ✅ Generate and sanitize secure filename
        filename = generate_secure_filename(current_user.id, ext)  # e.g., user123_abcd1234.pdf
        safe_filename = secure_filename(filename)

        # ✅ Save file to disk
        save_upload_file(file, UPLOAD_DIR, safe_filename)

        # ✅ Save metadata to DB
        new_paper = ResearchPaper(
            title=title,
            author=author,
            research_field=research_field,
            file_path=safe_filename,  # Only the filename
            original_filename=file.filename,
            uploader_id=current_user.id,
            created_at=datetime.now(timezone.utc)
        )
        db.add(new_paper)
        db.commit()
        db.refresh(new_paper)

        return {
            "message": "Paper uploaded successfully",
            "paper_id": new_paper.id,
            "file_name": safe_filename,
        }

    except Exception as e:
        logging.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")