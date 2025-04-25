import logging
import os
from fastapi import APIRouter,  Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from models.research_paper import ResearchPaper
from core.dependencies import get_db
from api.v1.endpoints.Auth.auth import get_current_user  # Ensure authentication middleware is implemented
from models.user import User
from fastapi import Query
from sqlalchemy import and_, func, or_
from typing import List
from pathlib import Path
from schemas.researchpaper import ResearchPaperOut

router = APIRouter()

give_error = "Internal Server Error"

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
        paper_dict["file_path"] = f"http://127.0.0.1:8000/uploads/research_papers/{paper.file_path}"
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
                "file_path": f"http://127.0.0.1:8000/uploads/research_papers/{paper.file_path}",
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
    """
    Download a specific research paper by ID.
    """
    try:
        paper = db.query(ResearchPaper).filter(ResearchPaper.id == paper_id).first()
        
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        file_path = f"uploads/research_papers/{paper.file_path}"  # Ensure this stores the absolute or relative file path
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on the server")

        return FileResponse(path=file_path, filename=paper.original_filename, media_type="application/pdf")

    except Exception as e:
        logging.error(f"Error downloading paper {paper_id}: {str(e)}")
        raise HTTPException(status_code=500, detail= give_error)