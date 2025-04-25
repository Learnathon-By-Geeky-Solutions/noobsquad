from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from core.security import create_access_token, generate_otp, store_otp
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv
from core.dependencies import get_db
from core.email import send_email
from datetime import datetime, timezone
from schemas.auth import OTPVerificationRequest
from models.user import User
import logging


user_not_found = "User not found"

# OAuth2PasswordBearer for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Router
router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/verify-otp/")
async def verify_otp(request: OTPVerificationRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail= user_not_found)
    
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    
    # Handle timezone-aware comparison to avoid "TypeError: can't compare offset-naive and offset-aware datetimes"
    if user.otp_expiry:
        # If otp_expiry is naive (doesn't have tzinfo), make it aware
        user_otp_expiry = user.otp_expiry.replace(tzinfo=timezone.utc) if user.otp_expiry.tzinfo is None else user.otp_expiry
        
        if user_otp_expiry < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="OTP expired")
    else:
        raise HTTPException(status_code=400, detail="OTP not found or expired")
    
    if user.otp != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # Mark as verified
    user.is_verified = True
    user.otp = None
    user.otp_expiry = None
    db.commit()
    db.refresh(user)
    
    # Return token
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer", "message": "Email verified"}


#Request a new OTP
@router.post("/resend-otp/")
async def resend_otp(request: OTPVerificationRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail= user_not_found)
    
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    
    # Generate new OTP
    otp = generate_otp()
    store_otp(db, user, otp)
    subject = "New Verification OTP"
    body = f"Your new OTP is: {otp}. It expires in 10 minutes."
    await send_email(user.email, subject, body)
    
    return {"message": "New OTP sent to your email"}