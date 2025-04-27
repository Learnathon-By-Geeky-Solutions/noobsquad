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

# Load environment variables
load_dotenv()

API_URL = os.getenv("VITE_API_URL")

# Helper: notify user if not the actor

def notify_if_not_self(db, actor_id, recipient_id, notif_type, post_id):
    if actor_id != recipient_id:
        create_notification(db, recipient_id, actor_id, notif_type, post_id)

# Helper: like handling

def update_like_count(like_data, db: Session, action: str):
    model = Post if like_data.post_id else Comment
    obj_id = like_data.post_id if like_data.post_id else like_data.comment_id
    instance = db.query(model).filter(model.id == obj_id).first()
    if instance:
        delta = 1 if action == "add" else -1
        instance.like_count = max(0, instance.like_count + delta)
        db.commit()


def remove_like(existing_like, db: Session, like_data: LikeCreate):
    db.delete(existing_like)
    update_like_count(like_data, db, "remove")


def add_like(like_data: LikeCreate, db: Session, current_user: User):
    created_at = datetime.now(ZoneInfo("UTC"))
    new_like = Like(user_id=current_user.id, post_id=like_data.post_id, comment_id=like_data.comment_id, created_at=created_at)
    db.add(new_like)
    update_like_count(like_data, db, "add")
    db.commit()
    db.refresh(new_like)
    return new_like

def get_like_count(db: Session, like_data: LikeCreate):
    model = Post if like_data.post_id else Comment
    obj_id = like_data.post_id if like_data.post_id else like_data.comment_id
    return db.query(model).filter(model.id == obj_id).first().like_count

def build_comment_response(comment, db: Session, user: User):
    replies = db.query(Comment).filter(Comment.parent_id == comment.id).all()
    return {
        "id": comment.id,
        "content": comment.content,
        "created_at": comment.created_at,
        "user": serialize_user(comment.user),
        "total_likes": len(comment.likes),
        "user_liked": any(l.user_id == user.id for l in comment.likes),
        "replies": [build_reply_response(r, user) for r in replies]
    }


def build_reply_response(reply, user: User):
    return {
        "id": reply.id,
        "content": reply.content,
        "created_at": reply.created_at,
        "user": serialize_user(reply.user),
        "total_likes": len(reply.likes),
        "user_liked": any(l.user_id == user.id for l in reply.likes)
    }


def serialize_user(user: User):
    return {
        "id": user.id,
        "username": user.username,
        "profile_picture": f"{API_URL}/uploads/profile_pictures/{user.profile_picture}"
    }