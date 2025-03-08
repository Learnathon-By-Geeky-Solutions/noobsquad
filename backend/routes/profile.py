from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import models.user as models
from database.session import SessionLocal
from models.user import User  # ✅ Correct model import
from schemas.user import UserResponse  # ✅ Correct schema import
from api.v1.endpoints.auth import get_current_user  # Authentication dependency
import os
import uuid
from pathlib import Path
import secrets

router = APIRouter()

# ✅ Predefined fields for validation
RELEVANT_FIELDS = [
    "Computer Science", "Electrical Engineering", "Mechanical Engineering",
    "Civil Engineering", "Artificial Intelligence", "Data Science", "Robotics",
    "Physics", "Mathematics", "Economics", "Biotechnology"
]

# ✅ Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Ensure upload directory exists


@router.post("/step1", response_model=UserResponse)
def complete_profile_step1(
    university_name: str = Form(...),
    department: str = Form(...),
    fields_of_interest: List[str] = Form(...),  # ✅ Corrected list input
    current_user: User = None,
    db: Session = Depends(get_db)
):
    if current_user is None:
        current_user = get_current_user(db)  # ✅ Pass db if required in get_current_user

    current_user = db.query(User).filter(User.id == current_user.id).first()

    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")   
    
    # ✅ Update the existing user profile directly
    current_user.university_name = university_name
    current_user.department = department
    current_user.fields_of_interest = ",".join(fields_of_interest)  # ✅ Convert list to CSV string

    if current_user.university_name and current_user.department and current_user.fields_of_interest:
        current_user.profile_completed = True  

    db.commit()
    db.refresh(current_user)  # ✅ Refresh to get updated values

    return UserResponse.from_orm(current_user)  # ✅ Return the correct schema

@router.post("/upload_picture")
def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = None,  # ✅ Default to None
    db: Session = Depends(get_db)
):
    if current_user is None:
        current_user = get_current_user(db)  # ✅ Fetch current_user inside function

    current_user = db.query(User).filter(User.id == current_user.id).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    # ✅ Define allowed file extensions
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

    # ✅ Securely extract the file extension
    file_extension = Path(file.filename).suffix.lower()

    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed: jpg, jpeg, png, gif, webp.")

    # ✅ Generate a secure filename (avoid using user input)
    secure_filename = f"{current_user.id}_{secrets.token_hex(8)}{file_extension}"  # Secure name with token

    # ✅ Construct a secure absolute path
    file_location = os.path.join(UPLOAD_DIR, secure_filename)
    file_location = os.path.abspath(file_location)  # Get absolute path

    # ✅ Ensure the file stays within the designated directory
    if not file_location.startswith(os.path.abspath(UPLOAD_DIR)):
        raise HTTPException(status_code=400, detail="Invalid file path detected.")

    # ✅ Save the file securely
    with open(file_location, "wb") as buffer:
        buffer.write(file.file.read())

    # ✅ Update profile picture path
    current_user.profile_picture = file_location

    db.commit()
    db.refresh(current_user)

    return {
        "filename": secure_filename,
        "path": file_location,
        "profile_completed": current_user.profile_completed  # ✅ Return updated status
    }
