from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import os
import secrets
import shutil
import re

from models.post import Post, PostMedia, PostDocument, Event, Like, Comment
from models.user import User
from core.connection_crud import get_connections
from crud.notification import create_notification

# Error messages
STATUS_404_ERROR = "Post not found"
EVENT_404_ERROR = "Event details not found"
INVALID_FILE_ERROR = "Invalid file format."

# URL constants
BASE_URL = "http://127.0.0.1:8000"
MEDIA_URL_PREFIX = f"{BASE_URL}/uploads/media"
DOCUMENT_URL_PREFIX = f"{BASE_URL}/uploads/document"

def get_newer_posts(last_seen_post: Optional[int], db: Session) -> Any:
    
    if not last_seen_post:
        return db.query(Post)
        
    latest_post = db.query(Post).filter(Post.id == last_seen_post).first()
    if not latest_post:
        return db.query(Post)
        
    return db.query(Post).filter(Post.created_at > latest_post.created_at)



def get_user_like_status(post_id: int, user_id: int, db: Session) -> bool:
    
    return db.query(Like).filter(Like.post_id == post_id, Like.user_id == user_id).first() is not None



def get_comments_for_post(post_id: int, db: Session) -> List[Comment]:
    
    return db.query(Comment).filter(Comment.post_id == post_id).all()



def get_post_additional_data(post: Post, db: Session) -> Dict[str, Any]:
    
    if not post.post_type:
        return {}
        
    handlers = {
        "media": get_media_post_data,
        "document": get_document_post_data,
        "event": get_event_post_data,
    }
    
    handler = handlers.get(post.post_type)
    return handler(post, db) if handler else {}


def get_media_post_data(post: Post, db: Session) -> Dict[str, Optional[str]]:

    media = db.query(PostMedia).filter(PostMedia.post_id == post.id).first()
    if not media:
        return {"media_url": None}
    
    return {"media_url": f"{MEDIA_URL_PREFIX}/{media.media_url}"}



def get_document_post_data(post: Post, db: Session) -> Dict[str, Optional[str]]:

    document = db.query(PostDocument).filter(PostDocument.post_id == post.id).first()
    if not document:
        return {"document_url": None}
    
    return {"document_url": f"{DOCUMENT_URL_PREFIX}/{document.document_url}"}


def get_event_post_data(post: Post, db: Session) -> Dict[str, Any]:

    event = db.query(Event).filter(Event.post_id == post.id).first()
    if not event:
        return {}
        
    return {
        "event": {
            "title": event.title,
            "description": event.description,
            "event_datetime": event.event_datetime,
            "location": event.location
        }
    }



def create_post_entry(db: Session, user_id: int, content: Optional[str], post_type: str) -> Post:
    
    post = Post(content=content, user_id=user_id, post_type=post_type)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post

def get_post_by_id(db: Session, post_id: int, user_id: Optional[int] = None) -> Post:
   
    filters = [Post.id == post_id]
    if user_id is not None:
        filters.append(Post.user_id == user_id)
        
    post = db.query(Post).filter(*filters).first()
    if not post:
        raise HTTPException(status_code=404, detail=STATUS_404_ERROR)
    return post

def update_post_content(post: Post, content: Optional[str]) -> None:
    
    if content is not None:
        post.content = content

def send_post_notifications(db: Session, user: User, post: Post) -> None:
  
    friends = get_connections(db, user.id)
    
    for friend in friends:
        friend_id = friend["friend_id"] if friend["user_id"] == user.id else friend["user_id"]
        create_notification(
            db=db,
            recipient_id=friend_id,
            actor_id=user.id,
            notif_type="new_post",
            post_id=post.id
        )
    
    db.commit()

def validate_file_extension(filename: str, allowed_extensions: set) -> str:
    
    ext = Path(filename).suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=INVALID_FILE_ERROR)
    return ext

def save_upload_file(upload_file: UploadFile, destination_dir: str, filename: str) -> str:
    
    file_path = os.path.join(destination_dir, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return file_path

def generate_secure_filename(user_id: int, file_ext: str) -> str:
    
    return f"{user_id}_{secrets.token_hex(8)}{file_ext}"

def remove_old_file_if_exists(file_path: str) -> None:
    
    if os.path.exists(file_path):
        os.remove(file_path)

def extract_hashtags(text: str) -> List[str]:
    
    if not text:
        return []
    return [tag.strip("#") for tag in re.findall(r"#\w+", text)]

def get_post_and_event(post_id: int, user_id: int, db: Session) -> Tuple[Post, Event]:
    
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == user_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found or not authorized")
    
    event = db.query(Event).filter(Event.post_id == post.id).first()
    if not event:
        raise HTTPException(status_code=404, detail=EVENT_404_ERROR)
    
    return post, event

def convert_to_utc(event_date: str, event_time: str, user_timezone: str) -> datetime:
    
    try:
        local_datetime = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M")
        local_tz = ZoneInfo(user_timezone)
        local_dt_with_tz = local_datetime.replace(tzinfo=local_tz)
        return local_dt_with_tz.astimezone(ZoneInfo("UTC"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date/time format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing date/time: {str(e)}")

def try_convert_datetime(date: str, time: str, tz: str, fallback: datetime) -> datetime:
    
    if not all([date, time, tz]):
        return fallback
    return convert_to_utc(date, time, tz)

def update_fields(fields: Dict[str, Any], model_instance: Any, db: Session) -> bool:
    
    if not fields:
        return False
        
    updated = False
    for field, value in fields.items():
        if value is not None and getattr(model_instance, field) != value:
            setattr(model_instance, field, value)
            updated = True
            
    if updated:
        db.commit()
        db.refresh(model_instance)
        
    return updated

def update_post_and_event(
    db: Session,
    post: Post,
    event: Event,
    post_data: Dict[str, Any],
    event_data: Dict[str, Any]
) -> bool:
    
    post_updated = update_fields(post_data, post, db)
    event_updated = update_fields(event_data, event, db)
    return post_updated or event_updated

def format_updated_event_response(post: Post, event: Event) -> Dict[str, Any]:
   
    return {
        "message": "Event post updated successfully",
        "updated_post": {
            "id": post.id,
            "content": post.content,
            "title": event.title,
            "description": event.description,
            "event_datetime": event.event_datetime,
            "location": event.location
        }
    }
