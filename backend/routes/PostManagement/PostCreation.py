
from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from sqlalchemy.orm import Session
from typing import Optional
import os
from datetime import datetime
from api.v1.endpoints.Auth.auth import get_current_user
from models.user import User
from models.post import  PostMedia, PostDocument, Event
from schemas.post import PostResponse, MediaPostResponse, DocumentPostResponse, EventResponse
from database.session import SessionLocal
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from AI.moderation import moderate_text
from services.services import validate_file_extension, generate_secure_filename, save_upload_file, create_post_entry, send_post_notifications, extract_hashtags
from models.hashtag import Hashtag
from models.university import University

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

MEDIA_DIR = "uploads/media/"
DOCUMENT_DIR = "uploads/document/"
EVENT_UPLOAD_DIR = "uploads/event_images"
os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(DOCUMENT_DIR, exist_ok=True)
os.makedirs(EVENT_UPLOAD_DIR, exist_ok=True)

ALLOWED_MEDIA = {".jpg", ".jpeg", ".jfif", ".png", ".gif", ".webp", ".mp4", ".mov"}
ALLOWED_DOCS = {".pdf", ".docx", ".txt"}

@router.post("/create_media_post/", response_model=MediaPostResponse)
async def create_media_post(
    content: Optional[str] = Form(None),
    media_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ext = validate_file_extension(media_file.filename, ALLOWED_MEDIA)
    filename = generate_secure_filename(current_user.id, ext)
    save_upload_file(media_file, MEDIA_DIR, filename)

    post = create_post_entry(db, current_user.id, content, "media")
    media_entry = PostMedia(post_id=post.id, media_url=filename, media_type=ext)
    db.add(media_entry)
    db.commit()
    db.refresh(media_entry)

    send_post_notifications(db, current_user, post)
    return media_entry


@router.post("/create_document_post/", response_model=DocumentPostResponse)
async def create_document_post(
    content: Optional[str] = Form(None),
    document_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ext = validate_file_extension(document_file.filename, ALLOWED_DOCS)
    filename = generate_secure_filename(current_user.id, ext)
    save_upload_file(document_file, DOCUMENT_DIR, filename)

    post = create_post_entry(db, current_user.id, content, "document")
    doc_entry = PostDocument(post_id=post.id, document_url=filename, document_type=ext)
    db.add(doc_entry)
    db.commit()
    db.refresh(doc_entry)

    send_post_notifications(db, current_user, post)
    return doc_entry


@router.post("/create_text_post/", response_model=PostResponse)
async def create_text_post(
    content: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if moderate_text(content):
        raise HTTPException(status_code=400, detail="Inappropriate content detected")

    post = create_post_entry(db, current_user.id, content, "text")
    hashtags = extract_hashtags(post.content)
    
    # Fetch all university names
    universities = db.query(University.name).all()
    university_names = {name.lower() for (name,) in universities}

    for tag in hashtags:
        if tag.lower() in university_names:
            existing_hashtag = db.query(Hashtag).filter_by(name=tag.lower()).first()
            if existing_hashtag:
                existing_hashtag.usage_count += 1
            else:
                existing_hashtag = Hashtag(name=tag.lower(), usage_count=1)
                db.add(existing_hashtag)

            post.hashtags.append(existing_hashtag)
    send_post_notifications(db, current_user, post)

    post.comment_count = 0
    post.user_liked = False
    return post


@router.post("/create_event_post/", response_model=EventResponse)
async def create_event_post(
    content: Optional[str] = Form(None),
    event_title: str = Form(...),
    event_description: str = Form(...),
    event_date: str = Form(...),
    event_time: str = Form(...),
    user_timezone: str = Form("Asia/Dhaka"),
    location: Optional[str] = Form(None),
    event_image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        dt_local = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M")
        dt_utc = dt_local.replace(tzinfo=ZoneInfo(user_timezone)).astimezone(ZoneInfo("UTC"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date/time: {str(e)}")

    image_url = None
    if event_image:
        ext = validate_file_extension(event_image.filename, {".jpg", ".jpeg", ".png", ".gif", ".webp"})
        filename = generate_secure_filename(current_user.id, ext)
        save_upload_file(event_image, EVENT_UPLOAD_DIR, filename)
        image_url = f"http://127.0.0.1:8000/uploads/event_images/{filename}"

    post = create_post_entry(db, current_user.id, content, "event")
    event = Event(
        post_id=post.id,
        user_id=current_user.id,
        title=event_title,
        description=event_description,
        event_datetime=dt_utc,
        location=location,
        image_url=image_url
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    send_post_notifications(db, current_user, post)

    return event