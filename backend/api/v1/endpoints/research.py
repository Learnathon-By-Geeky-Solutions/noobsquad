import logging
import os
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from models.research_paper import ResearchPaper
from core.dependencies import get_db
from api.v1.endpoints.auth import get_current_user  # Ensure authentication middleware is implemented
from models.user import User
from models.research_collaboration import ResearchCollaboration
from models.collaboration_request import CollaborationRequest
from typing import List
from fastapi import Query
from sqlalchemy import and_, func, or_
from models.research_collaboration import research_collaborators
from werkzeug.utils import secure_filename
import uuid
from pathlib import Path
from datetime import datetime, timezone
from services.FileHandler import validate_file_extension, generate_secure_filename, save_upload_file
from schemas.researchpaper import ResearchPaperOut
from dotenv import load_dotenv
from utils.supabase import upload_file_to_supabase
from fastapi.responses import RedirectResponse


# Load environment variables
load_dotenv()

router = APIRouter()

give_error = "Internal Server Error"
# Directory for storing research papers
UPLOAD_DIR = Path("uploads/research_papers")  # ✅ Ensure UPLOAD_DIR is a Path object
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)  # ✅ Create directory if it doesn't exist
ALLOWED_DOCS = [".pdf", ".doc", ".docx"]
# Get base URL from environment variable
API_URL = os.getenv("VITE_API_URL")

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
        safe_filename = await upload_file_to_supabase(file, filename, section="research_papers")

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

@router.get("/recommended/", response_model=List[ResearchPaperOut])
def get_recommended_papers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),

):
    # Get user's profile and interests
    profile = db.query(User).filter(User.id == current_user.id).first()

    if not profile or not profile.fields_of_interest:
        # Return latest papers if interests not set
        return db.query(ResearchPaper).order_by(ResearchPaper.created_at.desc()).limit(10).all()

    # ✅ Fix: Split comma-separated string into clean list of interests
    interests = [field.strip().lower() for field in profile.fields_of_interest.split(",")]

    # Fetch papers matching user's interests
    matched_papers = db.query(ResearchPaper).filter(
        func.lower(ResearchPaper.research_field).in_(interests)
    ).order_by(ResearchPaper.created_at.desc()).limit(10).all()

    # Pad with recent papers if fewer than 10 matched
    if len(matched_papers) < 10:
        additional = db.query(ResearchPaper).filter(
            ~func.lower(ResearchPaper.research_field).in_(interests)
        ).order_by(ResearchPaper.created_at.desc()).limit(10 - len(matched_papers)).all()
        matched_papers.extend(additional)

        papers = matched_papers

    result = []
    for paper in papers:
        paper_dict = paper.__dict__.copy()
        paper_dict["file_path"] = f"{API_URL}/uploads/research_papers/{paper.file_path}"
        result.append(paper_dict)

    return result


@router.get("/papers/search/")
def search_papers(
    keyword: str = Query(..., min_length=1, title="Search Keyword"), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search research papers by title containing a specific keyword.

    """
    try:
        key_word = f"%{keyword}%"
        papers = db.query(ResearchPaper).filter(or_(ResearchPaper.original_filename.ilike(key_word),ResearchPaper.author.ilike(key_word),ResearchPaper.title.ilike(key_word))).all()

        if not papers:
            raise HTTPException(status_code=404, detail="No papers found")

        return [
            {
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
            for paper in papers
        ]

    except Exception as e:
        logging.error(f"Error searching papers with keyword '{keyword}': {str(e)}")
        raise HTTPException(status_code=500, detail=give_error)


@router.get("/papers/download/{paper_id}/")
def download_paper(
    paper_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    paper = db.query(ResearchPaper).filter(ResearchPaper.id == paper_id).first()
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return RedirectResponse(url=paper.file_path)
    

@router.post("/post-research/")
def post_research(
    title: str = Form(...),
    research_field: str = Form(...),
    details: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Post a new research work for collaboration.
    """
    try:
        new_research = ResearchCollaboration(
            title=title,
            research_field=research_field,
            details=details,
            creator_id=current_user.id
        )
        db.add(new_research)
        db.commit()
        db.refresh(new_research)

        return {"message": "Research work posted successfully", "research_id": new_research.id}

    except Exception as e:
        logging.error(f"Error posting research: {str(e)}")
        raise HTTPException(status_code=500, detail= give_error)

@router.post("/request-collaboration/{research_id}/")
def request_collaboration(
    research_id: int,
    message: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Request collaboration on a research work.
    """
    try:
        research = db.query(ResearchCollaboration).filter(ResearchCollaboration.id == research_id).first()
        if not research:
            raise HTTPException(status_code=404, detail="Research work not found")

        # Ensure user is not requesting collaboration on their own research
        if research.creator_id == current_user.id:
            raise HTTPException(status_code=400, detail="You cannot request collaboration on your own research.")

        new_request = CollaborationRequest(
            research_id=research_id,
            requester_id=current_user.id,
            message=message
        )
        db.add(new_request)
        db.commit()
        db.refresh(new_request)

        return {"message": "Collaboration request sent successfully"}

    except Exception as e:
        logging.error(f"Error sending collaboration request: {str(e)}")
        raise HTTPException(status_code=500, detail= give_error)

@router.get("/collaboration-requests/")
def get_collaboration_requests(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Fetch all pending collaboration requests for the logged-in user, including:
    - Requester's username
    - Research title
    - Request message
    - Request status
    """
    try:
        requests = (
            db.query(
                CollaborationRequest.id,
                ResearchCollaboration.title.label("research_title"),
                CollaborationRequest.requester_id,
                CollaborationRequest.message,
                CollaborationRequest.status,  # ✅ Include request status
                User.username.label("requester_username")
            )
            .join(ResearchCollaboration, ResearchCollaboration.id == CollaborationRequest.research_id)
            .join(User, User.id == CollaborationRequest.requester_id)
            .filter(ResearchCollaboration.creator_id == current_user.id)
            .filter(CollaborationRequest.status == "pending")  # ✅ Only fetch pending requests
            .all()
        )

        return [
            {
                "id": request.id,
                "research_title": request.research_title,
                "requester_id": request.requester_id,
                "requester_username": request.requester_username,
                "message": request.message,
                "status": request.status.value  # ✅ Convert Enum to string if using SQLAlchemy Enum
            }
            for request in requests
        ]
    except Exception as e:
        logging.error(f"Error fetching collaboration requests: {str(e)}")
        raise HTTPException(status_code=500, detail= give_error)


@router.get("/my_post_research_papers/")
def get_user_papers(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Fetch research papers associated with the logged-in user.
    """
    try:
        papers = db.query(ResearchCollaboration).filter(
            ResearchCollaboration.creator_id == current_user.id  # ✅ Filter by user ID
        ).all()

        return [
            {
                "id": paper.id,
                "title": paper.title,
                "research_field": paper.research_field,
                "details": paper.details,
                "creator_id": paper.creator_id,
            }
            for paper in papers
        ]

    except Exception as e:
        logging.error(f"Error fetching user papers: {str(e)}")
        raise HTTPException(status_code=500, detail= give_error)
    
@router.get("/post_research_papers_others/")
def get_other_research_papers(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Fetch research papers not associated with the logged-in user and check if a collaboration request has already been sent.
    """
    try:
        papers = db.query(ResearchCollaboration).filter(
            ResearchCollaboration.creator_id != current_user.id  # Exclude user's own papers
        ).all()

        result = []
        for paper in papers:
            # Check if a collaboration request has already been made by the user
            existing_request = db.query(CollaborationRequest).filter(
                CollaborationRequest.research_id == paper.id,
                CollaborationRequest.requester_id == current_user.id
            ).first()

            result.append({
                "id": paper.id,
                "title": paper.title,
                "research_field": paper.research_field,
                "details": paper.details,
                "creator_id": paper.creator_id,
                "can_request_collaboration": existing_request is None  # Only allow request if it doesn't exist
            })

        return result

    except Exception as e:
        logging.error(f"Error fetching other research papers: {str(e)}")
        raise HTTPException(status_code=500, detail= give_error)

@router.post("/accept-collaboration/{request_id}/")
def accept_collaboration(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Accept a collaboration request and add the requester as a collaborator.
    """
    try:
        # Find the collaboration request
        collaboration_request = db.query(CollaborationRequest).filter(CollaborationRequest.id == request_id).first()
        if not collaboration_request:
            raise HTTPException(status_code=404, detail="Collaboration request not found")

        # Find the research work associated with the request
        research = db.query(ResearchCollaboration).filter(ResearchCollaboration.id == collaboration_request.research_id).first()
        if not research:
            raise HTTPException(status_code=404, detail="Research work not found")

        # Ensure only the research owner can accept the request
        if research.creator_id != current_user.id:
            raise HTTPException(status_code=403, detail="You are not authorized to accept this request.")

        # Check if the user is already a collaborator
        existing_collaborator = db.query(research_collaborators).filter(
            and_(
                research_collaborators.c.research_id == research.id,
                research_collaborators.c.user_id == collaboration_request.requester_id
            )
        ).first()

        if existing_collaborator:
            raise HTTPException(status_code=400, detail="User is already a collaborator.")

        # Update the request status
        collaboration_request.status = "accepted"
        db.add(collaboration_request)

        # Add collaborator to the research
        research.collaborators.append(collaboration_request.requester)
        db.add(research)

        db.commit()
        return {"message": "Collaboration request accepted successfully"}

    except Exception as e:
        logging.error(f"Error accepting collaboration request: {str(e)}")
        raise HTTPException(status_code=500, detail= give_error)

@router.get("/papers/user/{user_id}")
def get_papers_by_user(user_id: int, db: Session = Depends(get_db)):
    papers = db.query(ResearchPaper).filter(ResearchPaper.uploader_id == user_id).all()
    return [
            {
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
            for paper in papers
        ]
