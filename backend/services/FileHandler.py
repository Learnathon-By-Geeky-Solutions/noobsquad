from fastapi import HTTPException, UploadFile
import os
import secrets
from pathlib import Path
import shutil
from typing import Set


STATUS_404_ERROR = "Post not found"

def _get_file_extension(filename: str) -> str:
    return Path(filename).suffix.lower()

def validate_file_extension(filename: str, allowed_extensions: Set[str]) -> str:
    ext = _get_file_extension(filename)
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


def remove_old_file_if_exists(file_path: str) -> None:
    if os.path.exists(file_path):
        os.remove(file_path)