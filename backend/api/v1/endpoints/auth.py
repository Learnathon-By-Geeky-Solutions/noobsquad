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
    # Check if the email domain contains any of the educational keywords
    # if not any(keyword in user.email.lower() for keyword in allowed_keywords):
    #     raise HTTPException(status_code=400, detail="This is not an educational email address.")
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    hashed_password = hash_password(user.password)
    new_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        profile_completed=False,  # ✅ Profile completion starts separately
        is_verified=False  # ✅ Email verification status
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    #Generate and send OTP
    otp = generate_otp()
    store_otp(db, new_user, otp)
    subject = "Verify Your Email"
    body = f"Your OTP is {otp}. It is valid for 10 minutes."
    await send_email(new_user.email, subject, body)  # Send OTP to user's email

    return {"message": "User created successfully. Please log in."}

# ✅ Login Route
@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter((models.User.username == form_data.username) | (models.User.email == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email")
    
    token = create_access_token({"sub": user.username if user.username else user.email})
    return {"access_token": token, "token_type": "bearer"}

# ✅ Get Current User (Check Profile Status)
@router.get("/users/me/")
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        # Decode the token and log the payload
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        

        username: str = payload.get("sub")
        
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = db.query(models.User).filter(models.User.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail= user_not_found)
        
        return user
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError as e:
        print(f"JWT error: {str(e)}")  # Log the specific error for further insight
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/verify-otp/")
async def verify_otp(request: OTPVerificationRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail= user_not_found)
    
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    
    # Check if OTP is valid
    if user.otp != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # Handle timezone-aware comparison to avoid "TypeError: can't compare offset-naive and offset-aware datetimes"
    if user.otp_expiry:
        # If otp_expiry is naive (doesn't have tzinfo), make it aware
        user_otp_expiry = user.otp_expiry.replace(tzinfo=timezone.utc) if user.otp_expiry.tzinfo is None else user.otp_expiry
        
        if user_otp_expiry < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="OTP expired")
    else:
        raise HTTPException(status_code=400, detail="OTP not found or expired")
    
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
    
    # Check if OTP is valid first
    if user.otp != request.otp:
        logger.error(f"Invalid OTP for email: {request.email}")
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # Handle timezone-aware comparison to avoid "TypeError: can't compare offset-naive and offset-aware datetimes"
    if user.otp_expiry:
        # If otp_expiry is naive (doesn't have tzinfo), make it aware
        user_otp_expiry = user.otp_expiry.replace(tzinfo=timezone.utc) if user.otp_expiry.tzinfo is None else user.otp_expiry
        
        if user_otp_expiry < datetime.now(timezone.utc):
            logger.error(f"OTP expired for email: {request.email}")
            raise HTTPException(status_code=400, detail="OTP expired")
    else:
        raise HTTPException(status_code=400, detail="OTP not found or expired")
        
    user.hashed_password = hash_password(request.new_password)
    user.otp = None
    user.otp_expiry = None
    db.commit()
    db.refresh(user)
    logger.info(f"Password reset successful for email: {request.email}")
    return {"message": "Password reset successfully"}