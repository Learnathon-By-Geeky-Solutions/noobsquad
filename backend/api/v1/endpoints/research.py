# routers/research_router.py
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from models.research_paper import ResearchPaper
from models.research_collaboration import ResearchCollaboration
from models.collaboration_request import CollaborationRequest
from core.dependencies import get_db
from api.v1.endpoints.auth import get_current_user
from schemas.researchpaper import ResearchPaperOut
from services.research_service import *
from services.file_service import *
from dotenv import load_dotenv
from utils.supabase import upload_file_to_supabase
from fastapi.responses import RedirectResponse
from services.research_service import search_papers as search_papers_service


# Load environment variables
load_dotenv()

router = APIRouter()

@router.post("/upload-paper/")
async def upload_paper(
    title: str = Form(...),
    author: str = Form(...),
    research_field: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: ResearchPaper = Depends(get_current_user)
):
    # Validate required fields
    if not title.strip():
        raise HTTPException(status_code=422, detail="Title cannot be empty")
    if not author.strip():
        raise HTTPException(status_code=422, detail="Author cannot be empty")
    if not research_field.strip():
        raise HTTPException(status_code=422, detail="Research field cannot be empty")

    file_path = await save_uploaded_research_paper(file, current_user.id)
    paper = ResearchPaper(
        title=title,
        author=author,
        research_field=research_field,
        file_path=file_path,
        original_filename=file.filename,
        uploader_id=current_user.id
    )
    save_new_paper(db, paper)
    return {"message": "Paper uploaded successfully", "paper_id": paper.id, "file_name": file.filename}

@router.get("/recommended/", response_model=List[ResearchPaperOut])
def get_recommended_papers(db: Session = Depends(get_db), current_user: ResearchPaper = Depends(get_current_user)):
    profile = get_user_profile(db, current_user.id)
    interests = [i.strip().lower() for i in (profile.fields_of_interest or "").split(",") if i.strip()]
    papers = db.query(ResearchPaper).filter(func.lower(ResearchPaper.research_field).in_(interests)).limit(10).all() if interests else []
    if len(papers) < 10:
        additional = db.query(ResearchPaper).filter(~func.lower(ResearchPaper.research_field).in_(interests)).limit(10 - len(papers)).all()
        papers.extend(additional)
    return papers

@router.get("/papers/search/")
def search_papers(keyword: str = Query(..., min_length=1), db: Session = Depends(get_db), current_user: ResearchPaper = Depends(get_current_user)):
    papers = search_papers_service(db, keyword)
    if not papers:
        raise HTTPException(status_code=404, detail="No papers found")
    return papers

@router.get("/papers/download/{paper_id}/")
def download_paper(paper_id: int, db: Session = Depends(get_db), current_user: ResearchPaper = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    paper = get_paper_by_id(db, paper_id)
    
    # Check file size limit (100MB)
    import os
    try:
        file_size = os.path.getsize(paper.file_path)
        if file_size > 100 * 1024 * 1024:  # 100MB in bytes
            raise HTTPException(status_code=400, detail="File too large to download. Maximum size is 100MB.")
    except OSError:
        raise HTTPException(status_code=404, detail="File not found")
        
    return RedirectResponse(url=paper.file_path)

@router.post("/post-research/")
async def post_research(title: str = Form(...), research_field: str = Form(...), details: str = Form(...), db: Session = Depends(get_db), current_user: ResearchPaper = Depends(get_current_user)):
    # Validate research field format (only allow alphanumeric, spaces, and commas)
    import re
    if not re.match(r'^[a-zA-Z0-9\s,]+$', research_field):
        raise HTTPException(status_code=422, detail="Invalid research field. Only letters, numbers, spaces and commas are allowed.")
        
    research = ResearchCollaboration(title=title, research_field=research_field, details=details, creator_id=current_user.id)
    save_new_research(db, research)
    return {"message": "Research work posted successfully", "research_id": research.id}

@router.post("/request-collaboration/{research_id}/")
def request_collaboration(research_id: int, message: str = Form(...), db: Session = Depends(get_db), current_user: ResearchPaper = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    research = get_research_by_id(db, research_id)
    if research.creator_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot request collaboration on your own research.")
    collab_request = CollaborationRequest(research_id=research_id, requester_id=current_user.id, message=message)
    save_collaboration_request(db, collab_request)
    return {"message": "Collaboration request sent successfully"}

@router.get("/collaboration-requests/")
def get_collaboration_requests(db: Session = Depends(get_db), current_user: ResearchPaper = Depends(get_current_user)):
    return get_pending_collaboration_requests(db, current_user.id)

@router.get("/papers/user/{user_id}")
def get_papers_by_user(user_id: int, db: Session = Depends(get_db)):
    papers = db.query(ResearchPaper).filter(ResearchPaper.uploader_id == user_id).all()
    return papers
