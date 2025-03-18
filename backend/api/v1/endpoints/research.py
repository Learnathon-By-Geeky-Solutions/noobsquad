import logging
import os
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from models.research_paper import ResearchPaper
from core.dependencies import get_db
from api.v1.endpoints.auth import get_current_user  # Ensure authentication middleware is implemented
from models.user import User
from models.research_collaboration import ResearchCollaboration
from models.collaboration_request import CollaborationRequest
from fastapi import Query
from sqlalchemy import and_
from models.research_collaboration import research_collaborators
from werkzeug.utils import secure_filename
import uuid


router = APIRouter()

give_error = "Internal Server Error"
# Directory for storing research papers
UPLOAD_DIR = "Research_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
    Securely upload a research paper with metadata.
    """
    try:
        # ✅ Ensure UPLOAD_DIR exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # ✅ Generate a secure unique filename
        file_ext = os.path.splitext(file.filename)[1]  # Extract extension
        safe_filename = f"{uuid.uuid4().hex}{file_ext}"  # Unique file name
        sanitized_filename = secure_filename(safe_filename)  # Ensure it's safe
        
        file_location = os.path.join(UPLOAD_DIR, sanitized_filename)

        # ✅ Write the file securely
        with open(file_location, "wb") as f:
            f.write(await file.read())  # ✅ Use `await` for async file read

        # ✅ Save paper metadata to PostgreSQL
        new_paper = ResearchPaper(
            title=title,
            author=author,
            research_field=research_field,
            file_path=file_location,
            uploader_id=current_user.id  # ✅ Link paper to uploader
        )
        db.add(new_paper)
        db.commit()
        db.refresh(new_paper)

        return {"message": "Paper uploaded successfully", "paper_id": new_paper.id, "file_path": file_location}

    except Exception as e:
        logging.error(f"Error uploading paper: {str(e)}")
        raise HTTPException(status_code=500, detail=give_error)


@router.get("/papers/")
def get_papers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Fetch all research papers.
    """
    try:
        papers = db.query(ResearchPaper).all()
        return [
            {
                "id": paper.id,
                "title": paper.title,
                "author": paper.author,
                "research_field": paper.research_field,
                "uploader_id": paper.uploader_id,
            }
            for paper in papers
        ]
    except Exception as e:
        logging.error(f"Error fetching papers: {str(e)}")
        raise HTTPException(status_code=500, detail=give_error)

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
        papers = db.query(ResearchPaper).filter(ResearchPaper.title.ilike(f"%{keyword}%")).all()

        if not papers:
            raise HTTPException(status_code=404, detail="No papers found")

        return [
            {
                "id": paper.id,
                "title": paper.title,
                "author": paper.author,
                "research_field": paper.research_field,
                "file_path": paper.file_path,
                "uploader_id": paper.uploader_id,
                "download_url": f"/papers/download/{paper.id}/",
                "request_id": f"/request-collaboration/{paper.id}/"
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
    """
    Download a specific research paper by ID.
    """
    try:
        paper = db.query(ResearchPaper).filter(ResearchPaper.id == paper_id).first()
        
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        file_path = paper.file_path  # Ensure this stores the absolute or relative file path
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on the server")

        return FileResponse(path=file_path, filename=os.path.basename(file_path), media_type="application/pdf")

    except Exception as e:
        logging.error(f"Error downloading paper {paper_id}: {str(e)}")
        raise HTTPException(status_code=500, detail= give_error)


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
