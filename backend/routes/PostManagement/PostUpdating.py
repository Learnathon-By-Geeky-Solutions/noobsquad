
from fastapi import APIRouter, Depends, Form, File, UploadFile
from sqlalchemy.orm import Session
from typing import Optional
import os
from api.v1.endpoints.Auth.auth import get_current_user
from models.user import User
from models.post import PostMedia, PostDocument
from schemas.post import  TextPostUpdate
from database.session import SessionLocal
from sqlalchemy.orm import Session
from services.services import get_post_by_id, update_post_content, validate_file_extension, generate_secure_filename, save_upload_file, remove_old_file_if_exists, get_post_and_event, update_post_and_event, try_convert_datetime, format_updated_event_response

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

@router.put("/update_text_post/{post_id}")
async def update_text_post(
    post_id: int,
    update_data: TextPostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = get_post_by_id(db, post_id, current_user.id)
    update_post_content(post, update_data.content)
    db.commit()
    db.refresh(post)
    return post



@router.put("/update_media_post/{post_id}")
async def update_media_post(
    post_id: int,
    content: Optional[str] = Form(None),
    media_file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = get_post_by_id(db, post_id, current_user.id)
    update_post_content(post, content)

    if media_file and media_file.filename:
        ext = validate_file_extension(media_file.filename, ALLOWED_MEDIA)
        filename = generate_secure_filename(current_user.id, ext)
        save_upload_file(media_file, MEDIA_DIR, filename)

        media_entry = db.query(PostMedia).filter(PostMedia.post_id == post.id).first()
        if media_entry:
            remove_old_file_if_exists(os.path.join(MEDIA_DIR, media_entry.media_url))
            media_entry.media_url = filename
            media_entry.media_type = ext
        else:
            media_entry = PostMedia(post_id=post.id, media_url=filename, media_type=ext)
            db.add(media_entry)

        db.commit()

    db.refresh(post)
    media_url = db.query(PostMedia).filter(PostMedia.post_id == post.id).first().media_url

    return {
        "message": "Media post updated successfully",
        "updated_post": {
            "id": post.id,
            "user_id": post.user_id,
            "content": post.content,
            "post_type": post.post_type,
            "created_at": post.created_at,
            "media_url": media_url,
        },
    }

@router.put("/update_document_post/{post_id}")
async def update_document_post(
    post_id: int,
    content: Optional[str] = Form(None),
    document_file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = get_post_by_id(db, post_id, current_user.id)
    update_post_content(post, content)

    if document_file and document_file.filename:
        ext = validate_file_extension(document_file.filename, ALLOWED_DOCS)
        filename = generate_secure_filename(current_user.id, ext)
        save_upload_file(document_file, DOCUMENT_DIR, filename)

        doc_entry = db.query(PostDocument).filter(PostDocument.post_id == post.id).first()
        if doc_entry:
            remove_old_file_if_exists(os.path.join(DOCUMENT_DIR, doc_entry.document_url))
            doc_entry.document_url = filename
            doc_entry.document_type = ext
        else:
            doc_entry = PostDocument(post_id=post.id, document_url=filename, document_type=ext)
            db.add(doc_entry)

        db.commit()

    db.refresh(post)
    document_url = db.query(PostDocument).filter(PostDocument.post_id == post.id).first().document_url

    return {
        "message": "Document post updated successfully",
        "updated_post": {
            "id": post.id,
            "user_id": post.user_id,
            "content": post.content,
            "post_type": post.post_type,
            "created_at": post.created_at,
            "document_url": document_url,
        },
    }




@router.put("/update_event_post/{post_id}")
async def update_event_post(
    post_id: int,
    content: Optional[str] = Form(None),
    event_title: Optional[str] = Form(None),
    event_description: Optional[str] = Form(None),
    event_date: Optional[str] = Form(None),
    event_time: Optional[str] = Form(None),
    user_timezone: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post, event = get_post_and_event(post_id, current_user.id, db)
    
    event_datetime_utc = try_convert_datetime(event_date, event_time, user_timezone, fallback=event.event_datetime)
    
    post_updated = update_post_and_event(
        db=db,
        post=post,
        event=event,
        post_data={"content": content},
        event_data={
            "title": event_title,
            "description": event_description,
            "event_datetime": event_datetime_utc,
            "location": location
        }
    )
    
    if post_updated:
        return format_updated_event_response(post, event)

    return {"message": "No changes detected"}