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
from .CommentHelperFunc import get_comment_by_id, authorize_comment_deletion, get_post_by_id

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------------------------------
# API Routes
# ----------------------------------------

@router.post("/{post_id}/comment", response_model=CommentNestedResponse)
def comment_post(comment_data: CommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if comment_data.parent_id:
        raise HTTPException(status_code=400, detail="Root comment cannot have a parent_id.")
    
    new_comment = Comment(
        user_id=current_user.id,
        post_id=comment_data.post_id,
        content=comment_data.content,
        created_at=datetime.now(ZoneInfo("UTC"))
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    notify_if_not_self(db, current_user.id, new_comment.post.user_id, "comment", new_comment.post_id)
    
    return new_comment


@router.post("/{post_id}/comment/{parent_comment_id}/reply", response_model=CommentNestedResponse)
def reply_comment(comment_data: CommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    parent = get_comment_by_id(db, comment_data.parent_id)
    
    if parent.parent_id:
        raise HTTPException(status_code=400, detail="Cannot reply to a reply. Max depth reached.")
    
    reply = Comment(
        user_id=current_user.id,
        post_id=parent.post_id,
        content=comment_data.content,
        parent_id=parent.id,
        created_at=datetime.now(ZoneInfo("UTC"))
    )
    db.add(reply)
    db.commit()
    db.refresh(reply)

    notify_if_not_self(db, current_user.id, parent.user_id, "reply", reply.post_id)

    return reply


@router.get("/{post_id}/comments")
def get_comments(post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    parent_comments = db.query(Comment).filter(Comment.post_id == post_id, Comment.parent_id == None).all()
    return {"comments": [build_comment_response(comment, db, current_user) for comment in parent_comments]}


@router.delete("/comment/{comment_id}")
def delete_comment(comment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    comment = get_comment_by_id(db, comment_id)
    post = get_post_by_id(db, comment.post_id)

    authorize_comment_deletion(comment, post, current_user.id)

    db.delete(comment)
    db.commit()

    return {"message": "Comment deleted successfully"}
