from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import models.user as models
from database.session import SessionLocal
from models.user import User  # ✅ Correct model import
from models.university import University
from schemas.user import UserResponse  # ✅ Correct schema import
from api.v1.endpoints.auth import get_current_user  # Authentication dependency
import os
import uuid
from pathlib import Path
import secrets
from core.dependencies import get_db
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_URL = os.getenv("VITE_API_URL")

router = APIRouter()

# ✅ Predefined fields for validation
RELEVANT_FIELDS = [
    "Computer Science", "Electrical Engineering", "Mechanical Engineering",
    "Civil Engineering", "Artificial Intelligence", "Data Science", "Robotics",
    "Physics", "Mathematics", "Economics", "Biotechnology"
]

UPLOAD_DIR = "uploads/profile_pictures"
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Ensure upload directory exists

def get_or_create_university(db: Session, uni_name: str, dept_name: str):
    uni = db.query(University).filter(University.name == uni_name).first()

    if not uni:
        # University not found — create new with the department
        new_uni = University(name=uni_name, departments=[dept_name], total_members=1)
        db.add(new_uni)
        db.commit()
        db.refresh(new_uni)
        return new_uni

    # University exists — add department if not already present
    if not uni.departments:
        uni.departments = [dept_name]
    elif dept_name not in uni.departments:
        uni.departments.append(dept_name)

    # Optionally: Don't update total_members here, it's safer in profile step
    db.add(uni)
    db.commit()
    db.refresh(uni)
    return uni
    
@router.post("/step1", response_model=UserResponse)
def complete_profile_step1(
    university_name: str = Form(...),
    department: str = Form(...),
    fields_of_interest: List[str] = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.id == current_user.id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # 🔥 Add this line to update/create university and department properly
    get_or_create_university(db, university_name, department)
    uni = db.query(University).filter(University.name == university_name).first()
    if uni:
        uni.total_members = db.query(User).filter(User.university_name == university_name).count()
        db.commit()

    # Update user fields
    db_user.university_name = university_name
    db_user.department = department
    db_user.fields_of_interest = ",".join(fields_of_interest)

    # Optional: mark profile as completed (your own logic)
    if db_user.university_name and db_user.department and db_user.fields_of_interest:
        db_user.profile_completed = True

    db.commit()
    db.refresh(db_user)

    return UserResponse.from_orm(db_user)



@router.post("/upload_picture")
def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.id == current_user.id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    file_extension = Path(file.filename).suffix.lower()

    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Allowed: jpg, jpeg, png, gif, webp."
        )

    secure_filename = f"{db_user.id}_{secrets.token_hex(8)}{file_extension}"
    file_location = os.path.abspath(os.path.join(UPLOAD_DIR, secure_filename))

    if not file_location.startswith(os.path.abspath(UPLOAD_DIR)):
        raise HTTPException(status_code=400, detail="Invalid file path detected.")

    with open(file_location, "wb") as buffer:
        buffer.write(file.file.read())

    db_user.profile_picture = secure_filename
    db.commit()
    db.refresh(db_user)

    return {
        "filename": secure_filename,
        "profile_url": f"{API_URL}/uploads/profile_pictures/{secure_filename}",
        "profile_completed": db_user.profile_completed
    }
