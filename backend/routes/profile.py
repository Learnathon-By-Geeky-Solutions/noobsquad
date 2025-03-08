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
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_user = db.query(models.User).filter(models.User.id == current_user.id).first()

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
    current_user: models.User = Depends(get_current_user), # ✅ Default to None
    db: Session = Depends(get_db)
    
):

    current_user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    # ✅ Generate a secure, unique filename
    file_extension = Path(file.filename).suffix  # Get file extension safely
    secure_filename = f"{current_user.id}_{uuid.uuid4().hex}{file_extension}"  # Unique name

    # ✅ Use a secure path
    file_location = os.path.join(UPLOAD_DIR, secure_filename)

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
