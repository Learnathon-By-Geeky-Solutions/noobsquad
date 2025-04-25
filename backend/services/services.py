#all helper functions related to post, will be here
from uuid import uuid4
import uuid
from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List, Union
import os
import secrets
from pathlib import Path
from datetime import datetime, timezone
from api.v1.endpoints.Auth.auth import get_current_user
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

STATUS_404_ERROR = "Post not found"

# Helper function to get the latest post after the provided `last_seen_post`
def get_newer_posts(last_seen_post: Optional[int], db: Session):
    if last_seen_post:
        latest_post = db.query(Post).filter(Post.id == last_seen_post).first()
        if latest_post:
            return db.query(Post).filter(Post.created_at > latest_post.created_at)
    return db.query(Post)

# Helper function to get the like status of a user for a post
def get_user_like_status(post_id: int, user_id: int, db: Session):
    return db.query(Like).filter(Like.post_id == post_id, Like.user_id == user_id).first() is not None

# Helper function to get comments for a post
def get_comments_for_post(post_id: int, db: Session):
    return db.query(Comment).filter(Comment.post_id == post_id).all()

# Helper function to get additional data based on the post type (media, document, event)
def get_post_additional_data(post: Post, db: Session):
    handlers = {
        "media": get_media_post_data,
        "document": get_document_post_data,
        "event": get_event_post_data,
    }
    handler = handlers.get(post.post_type)
    return handler(post, db) if handler else {}
    

def get_media_post_data(post: Post, db: Session):
    media = db.query(PostMedia).filter(PostMedia.post_id == post.id).first()
    return {
        "media_url": f"http://127.0.0.1:8000/uploads/media/{media.media_url}" if media else None
    }

def get_document_post_data(post: Post, db: Session):
    document = db.query(PostDocument).filter(PostDocument.post_id == post.id).first()
    return {
        "document_url": f"http://127.0.0.1:8000/uploads/document/{document.document_url}" if document else None
    }

def get_event_post_data(post: Post, db: Session):
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

def validate_file_extension(filename: str, allowed_extensions: set):
    ext = Path(filename).suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file format.")
    return ext


def save_upload_file(upload_file: UploadFile, destination_dir: str, filename: str) -> str:
    file_path = os.path.join(destination_dir, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return file_path


def generate_secure_filename(user_id: int, file_ext: str) -> str:
    return f"{user_id}_{secrets.token_hex(8)}{file_ext}"


def create_post_entry(db: Session, user_id: int, content: Optional[str], post_type: str) -> Post:
    post = Post(content=content, user_id=user_id, post_type=post_type)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def send_post_notifications(db: Session, user: User, post: Post):
    friends = get_connections(db, user.id)
    for friend in friends:
        friend_id = friend["friend_id"] if friend["user_id"] == user.id else friend["user_id"]
        create_notification(db=db, recipient_id=friend_id, actor_id=user.id, notif_type="new_post", post_id=post.id)
    db.commit()

def get_post_by_id(db: Session, post_id: int, user_id: int = None):
    query = db.query(Post).filter(Post.id == post_id)
    if user_id is not None:
        query = query.filter(Post.user_id == user_id)
    post = query.first()
    if not post:
        raise HTTPException(status_code=404, detail=STATUS_404_ERROR)
    return post


def update_post_content(post: Post, content: Optional[str]):
    if content is not None:
        post.content = content


def remove_old_file_if_exists(file_path: str):
    if os.path.exists(file_path):
        os.remove(file_path)

def try_convert_datetime(date: str, time: str, tz: str, fallback: datetime) -> datetime:
    if date and time and tz:
        return convert_to_utc(date, time, tz)
    return fallback


def update_post_and_event(
    db: Session,
    post,
    event,
    post_data: dict,
    event_data: dict
) -> bool:
    updated = False
    updated |= update_fields(post_data, post, db)
    updated |= update_fields(event_data, event, db)
    return updated


def format_updated_event_response(post, event):
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

def send_post_notifications(db: Session, user: User, post: Post):
    """Sends notifications to all friends when a user creates a post."""
    
    # ✅ Fetch connected friends
    friends = get_connections(db, user.id)

    # ✅ Create notifications for all connected friends
    for friend in friends:
        friend_id = friend["friend_id"] if friend["user_id"] == user.id else friend["user_id"]
        
        create_notification(
            db=db,
            recipient_id=friend_id,  # ✅ Friend should receive the notification
            actor_id=user.id,        # ✅ The user who created the post
            notif_type="new_post",
            post_id=post.id
        )

    db.commit()  # ✅ Commit once after all notifications are added

# Helper function to get post and associated event
def get_post_and_event(post_id: int, user_id: int, db: Session):
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == user_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found or not authorized")
    
    event = db.query(Event).filter(Event.post_id == post.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event details not found")
    
    return post, event

# Helper function to convert event date and time to UTC
def convert_to_utc(event_date: str, event_time: str, user_timezone: str) -> Optional[datetime]:
    try:
        local_datetime = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M")
        local_tz = ZoneInfo(user_timezone)  # Correct way to use ZoneInfo
        local_dt_with_tz = local_datetime.replace(tzinfo=local_tz)  # Add timezone info
        return local_dt_with_tz.astimezone(ZoneInfo("UTC"))  # Convert to UTC
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date/time format: {str(e)}")

# Helper function to update post and event fields
def update_fields(fields, model_instance, db: Session) -> bool:
    updated = False
    for field, value in fields.items():
        if value is not None and getattr(model_instance, field) != value:
            setattr(model_instance, field, value)
            updated = True
    if updated:
        db.commit()
        db.refresh(model_instance)
    return updated

import re

def extract_hashtags(text: str) -> list[str]:
    return [tag.strip("#") for tag in re.findall(r"#\w+", text)]
