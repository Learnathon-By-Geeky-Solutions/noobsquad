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


def remove_old_file_if_exists(file_path: str):
    if os.path.exists(file_path):
        os.remove(file_path)