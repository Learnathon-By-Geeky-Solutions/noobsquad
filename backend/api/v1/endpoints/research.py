import logging
import os
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Request, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_
from werkzeug.utils import secure_filename
from pathlib import Path
from datetime import datetime, timezone
from typing import List

from models.research_paper import ResearchPaper
from models.user import User
from models.research_collaboration import ResearchCollaboration, research_collaborators
from models.collaboration_request import CollaborationRequest
from core.dependencies import get_db
from api.v1.endpoints.auth import get_current_user
from services.FileHandler import validate_file_extension, generate_secure_filename, save_upload_file
from schemas.researchpaper import ResearchPaperOut
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_URL = os.getenv("VITE_API_URL")
UPLOAD_DIR = Path("uploads/research_papers")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_DOCS = [".pdf", ".doc", ".docx"]
router = APIRouter()
give_error = "Internal Server Error"

# -----------------------------------------------
# Utility Functions
# -----------------------------------------------

def format_paper(paper: ResearchPaper) -> dict:
    return {
        "id": paper.id,
        "title": paper.title,
        "author": paper.author,
        "research_field": paper.research_field,
        "file_path": f"{API_URL}/uploads/research_papers/{paper.file_path}",
        "uploader_id": paper.uploader_id,
        "download_url": f"/papers/download/{paper.id}/",
        "request_id": f"/request-collaboration/{paper.id}/",
        "original_filename": paper.original_filename
    }

def format_research(research: ResearchCollaboration) -> dict:
    return {
        "id": research.id,
        "title": research.title,
        "research_field": research.research_field,
        "details": research.details,
        "creator_id": research.creator_id
    }

def handle_db_error(e: Exception):
    logging.error(str(e))
    raise HTTPException(status_code=500, detail=give_error)

def fetch_research_or_404(db: Session, research_id: int) -> ResearchCollaboration:
    research = db.query(ResearchCollaboration).filter(ResearchCollaboration.id == research_id).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research work not found")
    return research

def fetch_paper_or_404(db: Session, paper_id: int) -> ResearchPaper:
    paper = db.query(ResearchPaper).filter(ResearchPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper

# -----------------------------------------------
# Endpoints
# -----------------------------------------------

@router.post("/upload-paper/")
async def upload_paper(
    title: str = Form(...),
    author: str = Form(...),
    research_field: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        ext = validate_file_extension(file.filename, ALLOWED_DOCS)
        filename = secure_filename(generate_secure_filename(current_user.id, ext))
        save_upload_file(file, UPLOAD_DIR, filename)

        new_paper = ResearchPaper(
            title=title,
            author=author,
            research_field=research_field,
            file_path=filename,
            original_filename=file.filename,
            uploader_id=current_user.id,
            created_at=datetime.now(timezone.utc)
        )
        db.add(new_paper)
        db.commit()
        return {"message": "Paper uploaded successfully", "paper_id": new_paper.id, "file_name": filename}
    except Exception as e:
        handle_db_error(e)

@router.get("/recommended/", response_model=List[ResearchPaperOut])
def get_recommended_papers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.query(User).filter(User.id == current_user.id).first()
    interests = [field.strip().lower() for field in (profile.fields_of_interest or "").split(",") if field.strip()]
    papers = []

    if interests:
        matched = db.query(ResearchPaper).filter(func.lower(ResearchPaper.research_field).in_(interests)).limit(10).all()
        papers.extend(matched)
    if len(papers) < 10:
        additional = db.query(ResearchPaper).filter(~func.lower(ResearchPaper.research_field).in_(interests)).limit(10 - len(papers)).all()
        papers.extend(additional)

    return [format_paper(paper) for paper in papers]

@router.get("/papers/search/")
def search_papers(
    keyword: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        key_word = f"%{keyword}%"
        papers = db.query(ResearchPaper).filter(
            or_(
                ResearchPaper.title.ilike(key_word),
                ResearchPaper.author.ilike(key_word),
                ResearchPaper.original_filename.ilike(key_word)
            )
        ).all()
        if not papers:
            raise HTTPException(status_code=404, detail="No papers found")
        return [format_paper(paper) for paper in papers]
    except Exception as e:
        handle_db_error(e)

@router.get("/papers/download/{paper_id}/")
def download_paper(
    paper_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        paper = fetch_paper_or_404(db, paper_id)
        file_path = f"uploads/research_papers/{paper.file_path}"
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on the server")
        return FileResponse(path=file_path, filename=paper.original_filename, media_type="application/pdf")
    except Exception as e:
        handle_db_error(e)

@router.post("/post-research/")
def post_research(
    title: str = Form(...),
    research_field: str = Form(...),
    details: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        research = ResearchCollaboration(title=title, research_field=research_field, details=details, creator_id=current_user.id)
        db.add(research)
        db.commit()
        return {"message": "Research work posted successfully", "research_id": research.id}
    except Exception as e:
        handle_db_error(e)

@router.post("/request-collaboration/{research_id}/")
def request_collaboration(
    research_id: int,
    message: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        research = fetch_research_or_404(db, research_id)
        if research.creator_id == current_user.id:
            raise HTTPException(status_code=400, detail="Cannot request collaboration on your own research.")

        request = CollaborationRequest(research_id=research_id, requester_id=current_user.id, message=message)
        db.add(request)
        db.commit()
        return {"message": "Collaboration request sent successfully"}
    except Exception as e:
        handle_db_error(e)

@router.get("/collaboration-requests/")
def get_collaboration_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        requests = (
            db.query(
                CollaborationRequest.id,
                ResearchCollaboration.title.label("research_title"),
                User.username.label("requester_username"),
                CollaborationRequest.message,
                CollaborationRequest.status
            )
            .join(ResearchCollaboration, ResearchCollaboration.id == CollaborationRequest.research_id)
            .join(User, User.id == CollaborationRequest.requester_id)
            .filter(ResearchCollaboration.creator_id == current_user.id, CollaborationRequest.status == "pending")
            .all()
        )
        return [
            {
                "id": r.id,
                "research_title": r.research_title,
                "requester_username": r.requester_username,
                "message": r.message,
                "status": r.status.value
            }
            for r in requests
        ]
    except Exception as e:
        handle_db_error(e)

@router.get("/my_post_research_papers/")
def get_user_papers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        papers = db.query(ResearchCollaboration).filter(ResearchCollaboration.creator_id == current_user.id).all()
        return [format_research(p) for p in papers]
    except Exception as e:
        handle_db_error(e)

@router.get("/post_research_papers_others/")
def get_other_research_papers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        papers = db.query(ResearchCollaboration).filter(ResearchCollaboration.creator_id != current_user.id).all()
        result = []
        for paper in papers:
            has_request = db.query(CollaborationRequest).filter(
                CollaborationRequest.research_id == paper.id,
                CollaborationRequest.requester_id == current_user.id
            ).first()
            result.append({**format_research(paper), "can_request_collaboration": has_request is None})
        return result
    except Exception as e:
        handle_db_error(e)

@router.post("/accept-collaboration/{request_id}/")
def accept_collaboration(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        collab_request = db.query(CollaborationRequest).filter(CollaborationRequest.id == request_id).first()
        if not collab_request:
            raise HTTPException(status_code=404, detail="Collaboration request not found")
        research = fetch_research_or_404(db, collab_request.research_id)
        if research.creator_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to accept")

        # Check if requester is already a collaborator
        if collab_request.requester in research.collaborators:
            raise HTTPException(status_code=400, detail="User is already a collaborator.")

        research.collaborators.append(collab_request.requester)
        collab_request.status = "accepted"
        db.commit()
        return {"message": "Collaboration request accepted successfully"}
    except Exception as e:
        handle_db_error(e)

@router.get("/papers/user/{user_id}")
def get_papers_by_user(user_id: int, db: Session = Depends(get_db)):
    papers = db.query(ResearchPaper).filter(ResearchPaper.uploader_id == user_id).all()
    return [format_paper(paper) for paper in papers]
