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
from services.services import *

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

    post_list = []

    for post in posts:
        # ✅ Get like count & user like status
        user_liked = get_user_like_status(post.id, current_user.id, db)

        post_data = {
            "id": post.id,
            "post_type": post.post_type,
            "content": post.content,
            "created_at": post.created_at,
            "user": {
                "id": post.user.id,
                "username": post.user.username,
                "profile_picture": f"http://127.0.0.1:8000/uploads/profile_pictures/{post.user.profile_picture}"
            },
            "total_likes": post.like_count,
            "user_liked": user_liked
        }

        # ✅ Fetch additional data based on post_type
        post_data.update(get_post_additional_data(post, db))

        post_list.append(post_data)

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

    user_liked = get_user_like_status(post.id, current_user.id, db)

    post_data = {
        "id": post.id,
        "post_type": post.post_type,
        "content": post.content,
        "created_at": post.created_at,
        "user": {
            "id": post.user.id,
            "username": post.user.username,
            "profile_picture": f"http://127.0.0.1:8000/uploads/profile_pictures/{post.user.profile_picture}"
        },
        "total_likes": post.like_count,
        "user_liked": user_liked
    }

    post_data.update(get_post_additional_data(post, db))

    return post_data


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

        # # Build the full image URL if it exists
        # if event.image_url:
        #     # Replace any backslashes with forward slashes
        #     # full_image_url = f"{str(request.base_url).rstrip('/')}{event.image_url.replace('\\', '/')}"
        #     event.image_url = full_image_url

        return event
    else:
        events = db.query(Event).all()
        if not events:
            raise HTTPException(status_code=404, detail="No events found")

        # Add full image URL to each event in the list
        # for event in events:
        #     if event.image_url:
        #         # Replace any backslashes with forward slashes
        #         full_image_url = f"{str(request.base_url).rstrip('/')}{event.image_url.replace('\\', '/')}"
        #         event.image_url = full_image_url

        return events