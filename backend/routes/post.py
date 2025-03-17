from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from sqlalchemy.orm import Session
from typing import Optional
import os
import secrets
from pathlib import Path
from datetime import datetime, timezone
from api.v1.endpoints.auth import get_current_user
from models.user import User
from models.post import Post, PostMedia, PostDocument, Event
from schemas.post import PostResponse, MediaPostResponse, DocumentPostResponse, EventResponse, TextPostUpdate
from database.session import SessionLocal
import pytz 

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

MEDIA_DIR = "uploads/media/"
os.makedirs(MEDIA_DIR, exist_ok=True)  # Ensure upload directory exists
DOCUMENT_DIR = "uploads/document/"
os.makedirs(DOCUMENT_DIR, exist_ok=True) 

@router.post("/create_text_post/", response_model=PostResponse)
def create_text_post(
    content: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_post = Post(content=content, user_id=current_user.id, post_type="text")
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post  # Returns as PostResponse schema


@router.post("/create_media_post/", response_model=MediaPostResponse)
def create_media_post(
    content: Optional[str] = Form(None),
    media_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    allowed_media = {".jpg", ".jpeg", ".jfif", ".png", ".gif", ".webp", ".mp4", ".mov"}
    media_ext = Path(media_file.filename).suffix.lower()
    if media_ext not in allowed_media:
        raise HTTPException(status_code=400, detail="Invalid media format.")
    
    # Save media to local storage
    media_filename = f"{current_user.id}_{secrets.token_hex(8)}{media_ext}"
    media_path = os.path.join(MEDIA_DIR, media_filename)
    with open(media_path, "wb") as buffer:
        buffer.write(media_file.file.read())

    # Create Post Entry
    new_post = Post(content=content, user_id=current_user.id, post_type="media")
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    # Add Media Entry
    new_media = PostMedia(post_id=new_post.id, media_url=media_path, media_type=media_ext)
    db.add(new_media)
    db.commit()
    db.refresh(new_media)

    return new_media  # Returns as MediaPostResponse schema



@router.post("/create_document_post/", response_model=DocumentPostResponse)
def create_document_post(
    content: Optional[str] = Form(None),
    document_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    allowed_docs = {".pdf", ".docx", ".txt"}
    doc_ext = Path(document_file.filename).suffix.lower()
    if doc_ext not in allowed_docs:
        raise HTTPException(status_code=400, detail="Invalid document format.")

    # Save document to local storage
    doc_filename = f"{current_user.id}_{secrets.token_hex(8)}{doc_ext}"
    document_path = os.path.join(DOCUMENT_DIR, doc_filename)
    with open(document_path, "wb") as buffer:
        buffer.write(document_file.file.read())

    # Create Post Entry
    new_post = Post(content=content, user_id=current_user.id, post_type="document")
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    # Add Document Entry
    new_document = PostDocument(post_id=new_post.id, document_url=document_path, document_type=doc_ext)
    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    return new_document  # Returns as DocumentPostResponse schema



@router.post("/create_event_post/", response_model=EventResponse)
def create_event_post(
    content: Optional[str] = Form(None),
    event_title: str = Form(...),
    event_description: str = Form(...),
    event_date: str = Form(...),   # ✅ Accepts date in "YYYY-MM-DD"
    event_time: str = Form(...),   # ✅ Accepts time in "HH:MM"
    user_timezone: str = Form(...),  # ✅ User’s timezone (e.g., "Asia/Dhaka")
    location: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # ✅ Combine Date & Time
        local_datetime = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M")

        # ✅ Convert to UTC
        local_tz = pytz.timezone(user_timezone)
        local_dt_with_tz = local_tz.localize(local_datetime)  # Add timezone info
        event_datetime_utc = local_dt_with_tz.astimezone(pytz.UTC)  # Convert to UTC

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date/time format: {str(e)}")

    # ✅ Create Post Entry
    new_post = Post(content=content, user_id=current_user.id, post_type="event")
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    # ✅ Add Event Entry with UTC time
    new_event = Event(
        post_id=new_post.id,
        user_id=current_user.id,
        title=event_title,
        description=event_description,
        event_datetime=event_datetime_utc,  # ✅ Store in UTC
        location=location
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    return new_event  # Returns as EventResponse schema

@router.get("/get_post/{post_id}")
def get_post(post_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == current_user.id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    media_entry = db.query(PostMedia).filter(PostMedia.post_id == post.id).first()
    
    return {
        "post_id": post.id,
        "content": post.content,
        "media_url": media_entry.media_url if media_entry else None
    }


@router.put("/update_text_post/{post_id}")
def update_text_post(
    post_id: int,
    update_data: TextPostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == current_user.id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if update_data.content is not None:
        post.content = update_data.content

    db.commit()
    db.refresh(post)
    return {"message": "Post updated successfully"}


@router.put("/update_media_post/{post_id}")
def update_media_post(
    post_id: int,
    content: Optional[str] = Form(None),  
    media_file: Optional[UploadFile] = File(None),  # ✅ Optional to allow skipping media update
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Find the post
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == current_user.id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    


    # ✅ Only update content if it's provided, otherwise keep the existing content
    if content is not None:
        post.content = content  

    # ✅ If a new media file is uploaded, replace the old one
    if media_file is not None and media_file.filename != "":  
        allowed_media = {".jpg", ".jpeg", ".jfif", ".png", ".gif", ".webp", ".mp4", ".mov"}
        media_ext = Path(media_file.filename).suffix.lower()
        if media_ext not in allowed_media:
            raise HTTPException(status_code=400, detail="Invalid media format.")
        media_filename = f"{current_user.id}_{secrets.token_hex(8)}{media_ext}"
        media_path = os.path.join(MEDIA_DIR, media_filename)
        with open(media_path, "wb") as buffer:
            buffer.write(media_file.file.read())

        # Find the existing media entry
        media_entry = db.query(PostMedia).filter(PostMedia.post_id == post.id).first()
        if media_entry:
            os.remove(media_entry.media_url)  # Delete old file
            media_entry.media_url = media_path  # Update media path
            media_entry.media_type = media_ext
  
        else:
            new_media = PostMedia(post_id=post.id, media_url=media_path, media_type=media_ext)
            db.add(new_media)  

    db.commit()
    db.refresh(post)
    
    return {"message": "Media post updated successfully"}




@router.put("/update_document_post/{post_id}")
def update_document_post(
    post_id: int,
    content: Optional[str] = Form(None),  
    document_file: Optional[UploadFile] = File(None),  # ✅ Optional to allow skipping media update
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == current_user.id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if content is not None:
        post.content = content 

    allowed_docs = {".pdf", ".docx", ".txt"}


    # Handle document file replacement
    if document_file is not None and document_file.filename != "":  
        doc_ext = Path(document_file.filename).suffix.lower()
        if doc_ext not in allowed_docs:
            raise HTTPException(status_code=400, detail="Invalid document format.")
        doc_filename = f"{current_user.id}_{secrets.token_hex(8)}{doc_ext}"
        document_path = os.path.join(DOCUMENT_DIR, doc_filename)
        with open(document_path, "wb") as buffer:
            buffer.write(document_file.file.read()) 

        # Find the existing media entry
        doc_entry = db.query(PostDocument).filter(PostDocument.post_id == post.id).first()
        if doc_entry:
            os.remove(doc_entry.document_url)  # Delete old file
            doc_entry.document_url = document_path  # Update media path
            doc_entry.document_type = doc_ext
        else:
            new_media = PostDocument(post_id=post.id, document_url=document_path, document_type= doc_ext)
            db.add(new_media)  

    db.commit()
    db.refresh(post)
    
    return {"message": "Document post updated successfully"}


from datetime import datetime
import pytz  # For timezone conversion

@router.put("/update_event_post/{post_id}")
def update_event_post(
    post_id: int,
    content: Optional[str] = Form(None),
    event_title: Optional[str] = Form(None),
    event_description: Optional[str] = Form(None),
    event_date: Optional[str] = Form(None),  # ✅ Accepts only date
    event_time: Optional[str] = Form(None),  # ✅ Accepts only time
    user_timezone: Optional[str] = Form(None),  # ✅ Timezone info for conversion
    location: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # ✅ Find the existing event post
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == current_user.id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    event = db.query(Event).filter(Event.post_id == post.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event details not found")

    event_datetime_utc = None  # Initialize as None

    # ✅ If event date & time are provided, convert them to UTC
    if event_date and event_time and user_timezone:
        try:
            # ✅ Combine Date & Time
            local_datetime = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M")

            # ✅ Convert to UTC
            local_tz = pytz.timezone(user_timezone)
            local_dt_with_tz = local_tz.localize(local_datetime)  # Add timezone info
            event_datetime_utc = local_dt_with_tz.astimezone(pytz.UTC)  # Convert to UTC

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid date/time format: {str(e)}")

    # ✅ Define which fields belong to which model
    post_fields = {
        "content": content,
    }
    
    event_fields = {
        "title": event_title,
        "description": event_description,
        "event_datetime": event_datetime_utc if event_datetime_utc else None,  # ✅ Store UTC time if updated
        "location": location,
    }

    updated = False
    
    # ✅ Update Post fields
    for field, value in post_fields.items():
        if value is not None and getattr(post, field) != value:
            setattr(post, field, value)
            updated = True
    
    # ✅ Update Event fields
    for field, value in event_fields.items():
        if value is not None and getattr(event, field) != value:
            setattr(event, field, value)
            updated = True

    # ✅ Commit only if changes were made
    if updated:
        db.commit()
        db.refresh(event)
        return {"message": "Event post updated successfully"}
    
    return {"message": "No changes detected"}






@router.delete("/delete_post/{post_id}/")
def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Find the post
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == current_user.id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found or unauthorized")

    # Delete the post
    db.delete(post)
    db.commit()

    return {"message": "Post deleted successfully"}
