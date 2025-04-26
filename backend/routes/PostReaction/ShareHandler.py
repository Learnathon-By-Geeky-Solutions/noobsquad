from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.post import Share, Post, PostMedia, PostDocument, Event, Like
from models.user import User
from datetime import datetime
from zoneinfo import ZoneInfo
import uuid
from crud.notification import create_notification

def create_share(db: Session, user_id: int, post_id: int) -> Share:
    """Create a new share entry"""
    share_token = str(uuid.uuid4())
    created_at = datetime.now(ZoneInfo("UTC"))
    
    new_share = Share(
        user_id=user_id,
        post_id=post_id,
        share_token=share_token,
        created_at=created_at
    )
    db.add(new_share)
    db.commit()
    db.refresh(new_share)
    return new_share

def get_post_by_share_token(db: Session, share_token: str):
    """Get post details from share token"""
    shared_post = db.query(Share).filter(Share.share_token == share_token).first()
    if not shared_post:
        raise HTTPException(status_code=404, detail="Invalid or expired share link")

    post = db.query(Post).filter(Post.id == shared_post.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    
    return post

def get_post_additional_data(db: Session, post: Post, current_user_id: int):
    """Get additional data for a post based on its type"""
    user_liked = db.query(Like).filter(
        Like.post_id == post.id, 
        Like.user_id == current_user_id
    ).first() is not None

    base_data = {
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
        "user_liked": user_liked,
    }

    type_specific_data = {
        "media": lambda: get_media_data(db, post),
        "document": lambda: get_document_data(db, post),
        "event": lambda: get_event_data(db, post)
    }

    if post.post_type in type_specific_data:
        base_data.update(type_specific_data[post.post_type]())

    return base_data

def get_media_data(db: Session, post: Post):
    """Get media-specific post data"""
    media = db.query(PostMedia).filter(PostMedia.post_id == post.id).first()
    return {"media_url": f"http://127.0.0.1:8000/uploads/media/{media.media_url}" if media else None}

def get_document_data(db: Session, post: Post):
    """Get document-specific post data"""
    document = db.query(PostDocument).filter(PostDocument.post_id == post.id).first()
    return {"document_url": f"http://127.0.0.1:8000/uploads/document/{document.document_url}" if document else None}

def get_event_data(db: Session, post: Post):
    """Get event-specific post data"""
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
