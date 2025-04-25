from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.user import User
from database.session import SessionLocal
from schemas.postReaction import  ShareResponse,  ShareCreate
from api.v1.endpoints.Auth.auth import get_current_user
from datetime import datetime
import uuid  # Secure share token
from models.post import Post, PostMedia, PostDocument, Event, Like, Share
from zoneinfo import ZoneInfo
from crud.notification import create_notification

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




# ✅ Share a Post with a Unique Link (Stored)
@router.post("/{post_id}/share", response_model=ShareResponse)
def share_post(share_data: ShareCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    post = db.query(Post).filter(Post.id == share_data.post_id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    
    share_token = str(uuid.uuid4())
    
    created_at = datetime.now(ZoneInfo("UTC"))
    new_share = Share(
        user_id=current_user.id,
        post_id=share_data.post_id,
        share_token=share_token,
        created_at=created_at
    )
    db.add(new_share)
    db.commit()
    db.refresh(new_share)
    share_link = f"http://localhost:5173/share/{new_share.share_token}"

    post_owner = db.query(User).filter(User.id == post.user_id).first()
    if post_owner and post_owner.id != current_user.id:
        create_notification(db, recipient_id=post_owner.id, actor_id=current_user.id, notif_type="share", post_id=new_share.post_id)

    return {
        "id": new_share.id,
        "user_id": new_share.user_id,
        "post_id": new_share.post_id,
        "share_link": share_link,
        "created_at": new_share.created_at
    }

@router.get("/share/{share_token}")
def get_shared_post(share_token: str, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    shared_post = db.query(Share).filter(Share.share_token == share_token).first()
    
    if not shared_post:
        raise HTTPException(status_code=404, detail="Invalid or expired share link")

    post = db.query(Post).filter(Post.id == shared_post.post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    
    user_liked = db.query(Like).filter(Like.post_id == post.id, Like.user_id == current_user.id).first() is not None

    
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
        "user_liked": user_liked,
        
    }

    # ✅ Fetch additional data based on post_type
    if post.post_type == "media":
        media = db.query(PostMedia).filter(PostMedia.post_id == post.id).first()
        post_data["media_url"] = f"http://127.0.0.1:8000/uploads/media/{media.media_url}" if media else None

    elif post.post_type == "document":
        document = db.query(PostDocument).filter(PostDocument.post_id == post.id).first()
        post_data["document_url"] = f"http://127.0.0.1:8000/uploads/document/{document.document_url}" if document else None

    elif post.post_type == "event":
        event = db.query(Event).filter(Event.post_id == post.id).first()
        if event:
            post_data["event"] = {
                "title": event.title,
                "description": event.description,
                "event_datetime": event.event_datetime,
                "location": event.location
            }
    return post_data  # ✅ This returns all fields defined in the Post model