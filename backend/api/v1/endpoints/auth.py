from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database.session import SessionLocal
import models.user as models
from schemas.auth import ResetPasswordRequest, Token, ForgotPasswordRequest
from schemas.user import UserCreate, ProfileCompletionRequest
from core.security import hash_password, verify_password, create_access_token, generate_otp, store_otp
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
import os
from dotenv import load_dotenv
from core.dependencies import get_db
import re
from core.email import send_email
from datetime import datetime, timezone

from schemas.auth import OTPVerificationRequest
from models.user import User
import logging
from services.AuthHandler import AuthHandler




load_dotenv()

# Load secret key and algorithm from .env file
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

user_not_found = "User not found"

# OAuth2PasswordBearer for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Router
router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# allowed_keywords = ["stud", "edu", "university", "college", "ac", "edu", "institution"]

# ✅ Signup Route
@router.post("/signup/")
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user account."""
    response = await AuthHandler.create_user(
        db=db,
        username=user.username,
        email=user.email,
        password=user.password
    )
    return response

# ✅ Login Route
@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate user and return access token."""
    return await AuthHandler.authenticate_user(
        db=db,
        username_or_email=form_data.username,
        password=form_data.password
    )

# ✅ Get Current User (Check Profile Status)
@router.get("/users/me/")
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get current authenticated user."""
    return AuthHandler.get_current_user(db, token)

@router.post("/verify-otp/")
async def verify_otp(request: OTPVerificationRequest, db: Session = Depends(get_db)):
    """Verify user's email with OTP."""
    return await AuthHandler.verify_email(
        db=db,
        email=request.email,
        otp=request.otp
    )

#Request a new OTP
@router.post("/resend-otp/")
async def resend_otp(request: OTPVerificationRequest, db: Session = Depends(get_db)):
    """Resend verification OTP."""
    return await AuthHandler.resend_verification_otp(
        db=db,
        email=request.email
    )

# ✅ Forgot Password Route
@router.post("/forgot-password/")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Initiate password reset process."""
    return await AuthHandler.initiate_password_reset(
        db=db,
        email=request.email
    )

# ✅ Reset Password Route
@router.post("/reset-password/")
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using OTP."""
    return await AuthHandler.reset_password(
        db=db,
        email=request.email,
        otp=request.otp,
        new_password=request.new_password
    )