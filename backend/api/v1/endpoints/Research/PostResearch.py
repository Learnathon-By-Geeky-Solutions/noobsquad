import logging
from fastapi import APIRouter, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from core.dependencies import get_db
from api.v1.endpoints.Auth.auth import get_current_user  # Ensure authentication middleware is implemented
from models.user import User
from models.research_collaboration import ResearchCollaboration

router = APIRouter()

give_error = "Internal Server Error"

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