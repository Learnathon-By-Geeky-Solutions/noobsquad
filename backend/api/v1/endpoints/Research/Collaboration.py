import logging
from fastapi import APIRouter,  Form, Depends, HTTPException
from sqlalchemy.orm import Session
from core.dependencies import get_db
from api.v1.endpoints.Auth.auth import get_current_user  # Ensure authentication middleware is implemented
from models.user import User
from models.research_collaboration import ResearchCollaboration
from models.collaboration_request import CollaborationRequest
from sqlalchemy import and_
from models.research_collaboration import research_collaborators

router = APIRouter()

give_error = "Internal Server Error"


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