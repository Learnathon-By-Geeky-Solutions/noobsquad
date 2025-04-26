from pathlib import Path
import os
import secrets
import shutil
from fastapi import HTTPException, UploadFile

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

import re

def extract_hashtags(text: str) -> list[str]:
    return [tag.strip("#") for tag in re.findall(r"#\w+", text)]