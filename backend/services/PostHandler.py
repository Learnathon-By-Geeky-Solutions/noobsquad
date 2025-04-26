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

def create_post_entry(db: Session, user_id: int, content: Optional[str], post_type: str) -> Post:
    post = Post(content=content, user_id=user_id, post_type=post_type)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post

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

import re

def extract_hashtags(text: str) -> list[str]:
    return [tag.strip("#") for tag in re.findall(r"#\w+", text)]