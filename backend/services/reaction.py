from sqlalchemy.orm import Session
from models.post import Like, Comment, Post
from models.user import User
from schemas.postReaction import LikeCreate
from datetime import datetime
from models.user import User
from models.post import Post, Like, Comment
from zoneinfo import ZoneInfo
from crud.notification import create_notification
from dotenv import load_dotenv
import os
from typing import Any

# Load environment variables
load_dotenv()

API_URL = os.getenv("VITE_API_URL")

def _get_like_target(like_data: LikeCreate) -> tuple[type, int]:
    return (Post, like_data.post_id) if like_data.post_id else (Comment, like_data.comment_id)

def _update_like_count(db: Session, like_data: LikeCreate, action: str) -> None:
    model, obj_id = _get_like_target(like_data)
    instance = db.query(model).filter(model.id == obj_id).first()
    if instance:
        delta = 1 if action == "add" else -1
        instance.like_count = max(0, instance.like_count + delta)
        db.commit()

def notify_if_not_self(db: Session, actor_id: int, recipient_id: int, notif_type: str, post_id: int) -> None:
    if actor_id != recipient_id:
        create_notification(db, recipient_id, actor_id, notif_type, post_id)

def remove_like(existing_like: Like, db: Session, like_data: LikeCreate) -> None:
    db.delete(existing_like)
    _update_like_count(db, like_data, "remove")

def add_like(like_data: LikeCreate, db: Session, current_user: User) -> Like:
    created_at = datetime.now(ZoneInfo("UTC"))
    new_like = Like(
        user_id=current_user.id,
        post_id=like_data.post_id,
        comment_id=like_data.comment_id,
        created_at=created_at
    )
    db.add(new_like)
    _update_like_count(db, like_data, "add")
    db.commit()
    db.refresh(new_like)
    return new_like

def get_like_count(db: Session, like_data: LikeCreate) -> int:
    model, obj_id = _get_like_target(like_data)
    return db.query(model).filter(model.id == obj_id).first().like_count

def _serialize_user(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "profile_picture": f"{API_URL}/uploads/profile_pictures/{user.profile_picture}"
    }

def _build_reply_response(reply: Comment, user: User) -> dict[str, Any]:
    return {
        "id": reply.id,
        "content": reply.content,
        "created_at": reply.created_at,
        "user": _serialize_user(reply.user),
        "total_likes": len(reply.likes),
        "user_liked": any(l.user_id == user.id for l in reply.likes)
    }

def build_comment_response(comment: Comment, db: Session, user: User) -> dict[str, Any]:
    replies = db.query(Comment).filter(Comment.parent_id == comment.id).all()
    return {
        "id": comment.id,
        "content": comment.content,
        "created_at": comment.created_at,
        "user": _serialize_user(comment.user),
        "total_likes": len(comment.likes),
        "user_liked": any(l.user_id == user.id for l in comment.likes),
        "replies": [_build_reply_response(r, user) for r in replies]
    }