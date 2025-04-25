from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from schemas.auth import ResetPasswordRequest,  ForgotPasswordRequest
from core.security import hash_password, generate_otp, store_otp
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv
from core.dependencies import get_db
from core.email import send_email
from datetime import datetime, timezone
from models.user import User
import logging


user_not_found = "User not found"

# OAuth2PasswordBearer for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Router
router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Forgot Password Route
@router.post("/forgot-password/")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    logger.info(f"Password reset requested for email: {request.email}")
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        logger.error(f"No user found for email: {request.email}")
        raise HTTPException(status_code=404, detail= user_not_found)
    
    otp = generate_otp()
    store_otp(db, user, otp)
    await send_email(request.email, "Password Reset OTP", f"Your OTP for password reset is {otp}. It expires in 10 minutes.")
    logger.info(f"Password reset OTP sent to: {request.email}")
    return {"message": "Password reset OTP sent to your email"}

# ✅ Reset Password Route
@router.post("/reset-password/")
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    logger.info(f"Password reset attempt for email: {request.email}")
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        logger.error(f"No user found for email: {request.email}")
        raise HTTPException(status_code=404, detail= user_not_found)
    
    # Handle timezone-aware comparison to avoid "TypeError: can't compare offset-naive and offset-aware datetimes"
    if user.otp_expiry:
        # If otp_expiry is naive (doesn't have tzinfo), make it aware
        user_otp_expiry = user.otp_expiry.replace(tzinfo=timezone.utc) if user.otp_expiry.tzinfo is None else user.otp_expiry
        
        if user_otp_expiry < datetime.now(timezone.utc):
            logger.error(f"OTP expired for email: {request.email}")
            raise HTTPException(status_code=400, detail="OTP expired")
    else:
        raise HTTPException(status_code=400, detail="OTP not found or expired")
        
    if user.otp != request.otp:
        logger.error(f"Invalid OTP for email: {request.email}")
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    user.hashed_password = hash_password(request.new_password)
    user.otp = None
    user.otp_expiry = None
    db.commit()
    db.refresh(user)
    logger.info(f"Password reset successful for email: {request.email}")
    return {"message": "Password reset successfully"}