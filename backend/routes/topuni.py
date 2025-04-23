from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from collections import defaultdict
from models.user import User
from models.post import Post
from models.university import University
from schemas.university import UniversityPage, Member, UniversityPost, UniversityListResponse, UniversityResponse
from database.session import SessionLocal
from core.dependencies import get_db
from schemas.post import PostResponse
from services.services import extract_hashtags
from models.hashtag import post_hashtags


router = APIRouter()

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

@router.get("/top-universities", response_model=List[UniversityResponse])
def get_top_universities(limit: int = 5, db: Session = Depends(get_db)):
    try:
        top_unis = db.query(University).order_by(University.total_members.desc()).limit(limit).all()

        if not top_unis:
            raise HTTPException(status_code=404, detail="University not found")

        return top_unis

    except HTTPException as he:
        # Let real HTTP exceptions through
        raise he
    except Exception as e:
        # Everything else becomes 500
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")