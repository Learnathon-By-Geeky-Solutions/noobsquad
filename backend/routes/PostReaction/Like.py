from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.post import Like, Comment, Share, Post, Event, EventAttendee
from models.user import User
from schemas.post import PostResponse
from database.session import SessionLocal
from schemas.postReaction import LikeCreate, LikeResponse, CommentCreate, ShareResponse, CommentNestedResponse, ShareCreate
from schemas.eventAttendees import EventAttendeeCreate, EventAttendeeResponse
from api.v1.endpoints.auth import get_current_user
from datetime import datetime
import uuid  # Secure share token
from typing import List
from models.user import User
from models.post import Post, PostMedia, PostDocument, Event, Like, Comment
from zoneinfo import ZoneInfo
from crud.notification import create_notification
from schemas.notification import NotificationCreate
from services.reaction import get_like_count, add_like, remove_like, notify_if_not_self, build_comment_response

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/like", response_model=LikeResponse)
def like_action(
    like_data: LikeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not like_data.post_id and not like_data.comment_id:
        raise HTTPException(status_code=400, detail="Either post_id or comment_id must be provided.")

    existing_like = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.post_id == like_data.post_id,
        Like.comment_id == like_data.comment_id
    ).first()

    total_likes = get_like_count(db, like_data)

    if existing_like:
        response = {
            "id": existing_like.id,
            "user_id": existing_like.user_id,
            "post_id": existing_like.post_id,
            "comment_id": existing_like.comment_id,
            "created_at": existing_like.created_at,
            "total_likes": max(0, total_likes - 1),
            "user_liked": False,
            "message": "Like removed"
        }
        remove_like(existing_like, db, like_data)
        return response

    new_like = add_like(like_data, db, current_user)

    if like_data.post_id:
        post = db.query(Post).filter(Post.id == like_data.post_id).first()
        if post:
            notify_if_not_self(db, current_user.id, post.user_id, "like", post.id)

    total_likes = get_like_count(db, like_data)

    return {
        "id": new_like.id,
        "user_id": new_like.user_id,
        "post_id": new_like.post_id,
        "comment_id": new_like.comment_id,
        "created_at": new_like.created_at,
        "total_likes": total_likes,
        "user_liked": True,
        "message": "Like added successfully"
    }