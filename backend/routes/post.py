from uuid import uuid4
import uuid
from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List, Union
import os
import secrets
from pathlib import Path
from datetime import datetime, timezone
from api.v1.endpoints.auth import get_current_user
from models.user import User
from models.post import Post, PostMedia, PostDocument, Event, Like, Comment
from schemas.post import PostResponse, MediaPostResponse, DocumentPostResponse, EventResponse, TextPostUpdate
from database.session import SessionLocal
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session, joinedload
import shutil
from core.connection_crud import get_connections
from crud.notification import create_notification
from AI.moderation import moderate_text
from services.services import   get_post_and_event, update_post_and_event, try_convert_datetime, format_updated_event_response
from services.PostHandler import get_newer_posts, get_user_like_status, get_comments_for_post, create_post_entry, update_post_content , extract_hashtags, get_post_by_id
from services.FileHandler import remove_old_file_if_exists, save_upload_file, generate_secure_filename, validate_file_extension
from services.NotificationHandler import send_post_notifications
from services.PostTypeHandler import get_post_additional_data
from models.hashtag import Hashtag
from models.university import University
from dotenv import load_dotenv
import os
from utils.cloudinary import upload_to_cloudinary
from utils.post_utils import validate_post_ownership, prepare_post_response, handle_media_upload, create_base_post
from services.EventHandler import create_event_post as create_event_post_entry, format_event_response, handle_event_upload, update_event_post as update_event_post_entry
from utils.supabase import upload_file_to_supabase

# Load environment variables
load_dotenv()

API_URL = os.getenv("VITE_API_URL") # ✅ Get base URL from environment variable

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
ALLOWED_DOCS = {".pdf", ".docx", ".txt", ".pptx"}







# Main function refactor
@router.get("/")
def get_posts(
    limit: int = Query(10, alias="limit"),  # Default to 10 posts
    offset: int = Query(0, alias="offset"),  # Start at 0
    last_seen_post: Optional[int] = Query(None, alias="last_seen"),  # Last post ID seen
    user_id: Optional[int] = Query(None, alias="user_id"),  # User ID to filter posts (for profile)
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ✅ Fetch posts with pagination.
    ✅ If `last_seen_post` is provided, fetch **newer** posts than the last seen post.
    ✅ Include total likes, user liked status, and comments for each post.
    """

    # ✅ Get the posts query with the optional filter for newer posts
    query = get_newer_posts(last_seen_post, db)

    if user_id:
        query = query.filter(Post.user_id == user_id)
    
    # ✅ Apply pagination
    posts = query.order_by(Post.created_at.desc()).offset(offset).limit(limit).all()

    post_list = [prepare_post_response(post, current_user, db) for post in posts]

    return {"posts": post_list, "count": len(post_list)}



@router.get("/{post_id}")
def get_single_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return prepare_post_response(post, current_user, db)


@router.post("/create_media_post/", response_model=MediaPostResponse)
async def create_media_post(
    content: Optional[str] = Form(None),
    media_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new media post."""
    # Validate file extension
    ext = validate_file_extension(media_file.filename, ALLOWED_MEDIA)
    
    # Upload media to cloudinary
    upload_result = await handle_media_upload(media_file, "noobsquad/media_uploads")
    
    # Create post
    post = create_base_post(db, current_user.id, content, "media")
    
    # Create media entry
    media_entry = PostMedia(
        post_id=post.id,
        media_url=upload_result["secure_url"],
        media_type=ext
    )
    db.add(media_entry)
    db.commit()
    db.refresh(media_entry)
    
    # Send notifications
    send_post_notifications(db, current_user, post)
    return media_entry


@router.post("/create_document_post/", response_model=DocumentPostResponse)
async def create_document_post(
    content: Optional[str] = Form(None),
    document_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new document post."""
    # Validate file extension
    ext = validate_file_extension(document_file.filename, ALLOWED_DOCS)
    
    # Generate filename and save file
    filename = generate_secure_filename(current_user.id, ext)

    # Upload to Supabase
    document_url = await upload_file_to_supabase(document_file, filename, section="upload_documents")
    
    # Create post and document entries
    post = create_post_entry(db, current_user.id, content, "document")
    doc_entry = PostDocument(post_id=post.id, document_url=document_url, document_type=ext)
    db.add(doc_entry)
    db.commit()
    db.refresh(doc_entry)
    
    # Send notifications
    send_post_notifications(db, current_user, post)
    return doc_entry


@router.post("/create_text_post/", response_model=PostResponse)
async def create_text_post(
    content: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new text post."""
    post = create_base_post(db, current_user.id, content, "text")
    send_post_notifications(db, current_user, post)
    
    # Add required fields for response
    post.comment_count = 0  # New post has no comments
    post.user_liked = False  # User hasn't liked their own post yet
    
    return post


@router.post("/create_event_post/", response_model=EventResponse)
async def create_event_post(
    content: Optional[str] = Form(None),
    event_title: str = Form(...),
    event_description: str = Form(...),
    event_date: str = Form(...),
    event_time: str = Form(...),
    user_timezone: str = Form("UTC"),
    location: Optional[str] = Form(None),
    event_image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new event post."""
    event_data = {
        "event_title": event_title,
        "event_description": event_description,
        "event_date": event_date,
        "event_time": event_time,
        "user_timezone": user_timezone,
        "location": location
    }
    upload_result = await handle_event_upload(event_image, "noobsquad/event_media_uploads")
    post, event = create_event_post_entry(
        db=db,
        user_id=current_user.id,
        content=content,
        event_data=event_data,
        image_url=upload_result["secure_url"]
    )
    
    send_post_notifications(db, current_user, post)
    return format_event_response(post, event)

@router.get("/posts/")
def get_posts(user_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Post)
    if user_id:
        query = query.filter(Post.user_id == user_id)
    return query.all()



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
        
        upload_result = upload_to_cloudinary(
            media_file.file,
            folder_name="noobsquad/media_uploads"
        )

        secure_url = upload_result["secure_url"]
        resource_type = upload_result["resource_type"]

        media_entry = db.query(PostMedia).filter(PostMedia.post_id == post.id).first()
        if media_entry:
            # (Optional) Here you can delete old Cloudinary media if you want
            media_entry.media_url = secure_url
            media_entry.media_type = resource_type  # You can also keep ext if needed
        else:
            media_entry = PostMedia(
                post_id=post.id,
                media_url=secure_url,
                media_type=ext
            )
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
        
        # Upload to Supabase
        document_url = await upload_file_to_supabase(document_file, filename, section="upload_documents")

        doc_entry = db.query(PostDocument).filter(PostDocument.post_id == post.id).first()
        if doc_entry:
            # No need to remove old file as Supabase handles versioning
            doc_entry.document_url = document_url
            doc_entry.document_type = ext
        else:
            doc_entry = PostDocument(post_id=post.id, document_url=document_url, document_type=ext)
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
    db: Session = Depends(get_db)
):
    """Update an existing event post."""
    # Validate post ownership
    post = validate_post_ownership(post_id, current_user.id, db)
    
    # Get associated event
    event = db.query(Event).filter(Event.post_id == post.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event details not found")
    
    update_data = {
        "content": content,
        "event_title": event_title,
        "event_description": event_description,
        "event_date": event_date,
        "event_time": event_time,
        "user_timezone": user_timezone,
        "location": location
    }
    
    post, event = update_event_post_entry(db, post, event, update_data)
    return format_event_response(post, event)


@router.delete("/delete_post/{post_id}")
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post = get_post_by_id(db, post_id, current_user.id)
    db.delete(post)
    db.commit()
    return {"message": "Post deleted successfully"}

@router.get("/events/", response_model=Union[List[EventResponse], EventResponse])
async def get_events(
    request: Request,  # We need this to access the base URL of the server
    event_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if event_id is not None:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return event
    else:
        events = db.query(Event).all()
        if not events:
            raise HTTPException(status_code=404, detail="No events found")
        return events
        