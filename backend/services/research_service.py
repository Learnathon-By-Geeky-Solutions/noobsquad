# services/research_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from fastapi import HTTPException
from models.research_paper import ResearchPaper
from models.research_collaboration import ResearchCollaboration
from models.collaboration_request import CollaborationRequest
from models.user import User

def get_paper_by_id(db: Session, paper_id: int) -> ResearchPaper:
    paper = db.query(ResearchPaper).filter(ResearchPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper

def get_user_profile(db: Session, user_id: int) -> User:
    return db.query(User).filter(User.id == user_id).first()

def get_research_by_id(db: Session, research_id: int) -> ResearchCollaboration:
    research = db.query(ResearchCollaboration).filter(ResearchCollaboration.id == research_id).first()
    if not research:
        raise HTTPException(status_code=404, detail="Research work not found")
    return research

def search_papers(db: Session, keyword: str):
    key_word = f"%{keyword}%"
    papers = db.query(ResearchPaper).filter(
        or_(
            ResearchPaper.title.ilike(key_word),
            ResearchPaper.author.ilike(key_word),
            ResearchPaper.original_filename.ilike(key_word)
        )
    ).all()
    return papers

def save_new_paper(db: Session, paper: ResearchPaper):
    db.add(paper)
    db.commit()
    db.refresh(paper)
    return paper

def save_new_research(db: Session, research: ResearchCollaboration):
    db.add(research)
    db.commit()
    db.refresh(research)
    return research

def save_collaboration_request(db: Session, request: CollaborationRequest):
    db.add(request)
    db.commit()
    db.refresh(request)
    return request

def get_pending_collaboration_requests(db: Session, user_id: int):
    return (
        db.query(
            CollaborationRequest.id,
            ResearchCollaboration.title.label("research_title"),
            CollaborationRequest.message,
            CollaborationRequest.status,
            User.username.label("requester_username")
        )
        .join(ResearchCollaboration, CollaborationRequest.research_id == ResearchCollaboration.id)
        .join(User, CollaborationRequest.requester_id == User.id)
        .filter(ResearchCollaboration.creator_id == user_id, CollaborationRequest.status == "pending")
        .all()
    )
