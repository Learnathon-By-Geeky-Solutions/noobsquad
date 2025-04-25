import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.research_paper import ResearchPaper
from core.dependencies import get_db
from api.v1.endpoints.Auth.auth import get_current_user  # Ensure authentication middleware is implemented
from models.user import User
from models.research_collaboration import ResearchCollaboration
from models.collaboration_request import CollaborationRequest
from pathlib import Path

router = APIRouter()

give_error = "Internal Server Error"


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



@router.get("/papers/user/{user_id}")
def get_papers_by_user(user_id: int, db: Session = Depends(get_db)):
    papers = db.query(ResearchPaper).filter(ResearchPaper.uploader_id == user_id).all()
    return [
            {
                "id": paper.id,
                "title": paper.title,
                "author": paper.author,
                "research_field": paper.research_field,
                "file_path": f"http://127.0.0.1:8000/uploads/research_papers/{paper.file_path}",
                "uploader_id": paper.uploader_id,
                "download_url": f"/papers/download/{paper.id}/",
                "request_id": f"/request-collaboration/{paper.id}/",
                "original_filename": paper.original_filename
                

            }
            for paper in papers
        ]
