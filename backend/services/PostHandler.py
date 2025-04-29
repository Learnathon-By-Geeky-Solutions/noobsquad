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
import re

STATUS_404_ERROR = "Post not found"

def _get_post_query(db: Session, last_seen_post: Optional[int]) -> Session:
    if not last_seen_post:
        return db.query(Post)
    
    latest_post = db.query(Post).filter(Post.id == last_seen_post).first()
    if not latest_post:
        return db.query(Post)
    
    return db.query(Post).filter(Post.created_at > latest_post.created_at)

def get_newer_posts(last_seen_post: Optional[int], db: Session):
    return _get_post_query(db, last_seen_post)

def get_user_like_status(post_id: int, user_id: int, db: Session):
    return db.query(Like).filter(Like.post_id == post_id, Like.user_id == user_id).first() is not None

def get_comments_for_post(post_id: int, db: Session):
    return db.query(Comment).filter(Comment.post_id == post_id).all()

def create_post_entry(db: Session, user_id: int, content: Optional[str], post_type: str) -> Post:
    post = Post(content=content, user_id=user_id, post_type=post_type)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post

def _validate_post_ownership(post: Optional[Post], user_id: int) -> None:
    if not post:
        raise HTTPException(status_code=404, detail=STATUS_404_ERROR)
    if post.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this post")

def get_post_by_id(db: Session, post_id: int, user_id: int = None):
    query = db.query(Post).filter(Post.id == post_id)
    if user_id is not None:
        query = query.filter(Post.user_id == user_id)
    post = query.first()
    _validate_post_ownership(post, user_id)
    return post

def update_post_content(post: Post, content: Optional[str]):
    if content is not None:
        post.content = content

def extract_hashtags(text: str) -> list[str]:
    return [tag.strip("#") for tag in re.findall(r"#\w+", text)]