from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from fastapi import HTTPException
from sqlalchemy.orm import Session
import jwt
from models.user import User
from core.security import hash_password, verify_password, create_access_token, generate_otp, store_otp
from core.email import send_email
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# Configure logging
logger = logging.getLogger(__name__)

def _validate_username_availability(db: Session, username: str) -> None:
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

def _create_user_record(db: Session, username: str, email: str, hashed_password: str) -> User:
    new_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        profile_completed=False,
        is_verified=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

async def _send_verification_email(email: str, otp: str) -> None:
    await send_email(
        email,
        "Verify Your Email",
        f"Your OTP is {otp}. It is valid for 10 minutes."
    )

def _get_user_by_credentials(db: Session, username_or_email: str) -> Optional[User]:
    return db.query(User).filter(
        (User.username == username_or_email) | (User.email == username_or_email)
    ).first()

def _validate_user_credentials(user: Optional[User], password: str) -> None:
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email")

def _decode_jwt_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError as e:
        logger.error(f"JWT error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")

def _validate_otp_expiry(otp_expiry: Optional[datetime]) -> None:
    if not otp_expiry:
        raise HTTPException(status_code=400, detail="OTP not found or expired")
    
    otp_expiry = otp_expiry.replace(tzinfo=timezone.utc) if otp_expiry.tzinfo is None else otp_expiry
    if otp_expiry < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="OTP expired")

class AuthHandler:
    @staticmethod
    async def create_user(
        db: Session,
        username: str,
        email: str,
        password: str
    ) -> Dict[str, str]:
        """Create a new user and send verification OTP."""
        _validate_username_availability(db, username)
        hashed_password = hash_password(password)
        new_user = _create_user_record(db, username, email, hashed_password)
        
        otp = generate_otp()
        store_otp(db, new_user, otp)
        await _send_verification_email(email, otp)
        
        return {"message": "User created successfully. Please log in."}

    @staticmethod
    async def authenticate_user(
        db: Session,
        username_or_email: str,
        password: str
    ) -> Dict[str, str]:
        """Authenticate user and return access token."""
        user = _get_user_by_credentials(db, username_or_email)
        _validate_user_credentials(user, password)
        
        token = create_access_token({"sub": user.username or user.email})
        return {"access_token": token, "token_type": "bearer"}

    @staticmethod
    def get_current_user(db: Session, token: str) -> User:
        """Get current user from JWT token."""
        payload = _decode_jwt_token(token)
        username: str = payload.get("sub")
        
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user

    @staticmethod
    def validate_otp(user: User, otp: str) -> None:
        """Validate OTP and its expiry."""
        if user.otp != otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")
        _validate_otp_expiry(user.otp_expiry)

    @staticmethod
    async def verify_email(
        db: Session,
        email: str,
        otp: str
    ) -> Dict[str, str]:
        """Verify user's email with OTP."""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.is_verified:
            raise HTTPException(status_code=400, detail="Email already verified")
        
        AuthHandler.validate_otp(user, otp)
        
        user.is_verified = True
        user.otp = None
        user.otp_expiry = None
        db.commit()
        db.refresh(user)
        
        token = create_access_token({"sub": user.username})
        return {
            "access_token": token,
            "token_type": "bearer",
            "message": "Email verified"
        }

    @staticmethod
    async def resend_verification_otp(
        db: Session,
        email: str
    ) -> Dict[str, str]:
        """Resend verification OTP to user's email."""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.is_verified:
            raise HTTPException(status_code=400, detail="Email already verified")
        
        otp = generate_otp()
        store_otp(db, user, otp)
        await send_email(
            email,
            "New Verification OTP",
            f"Your new OTP is: {otp}. It expires in 10 minutes."
        )
        
        return {"message": "New OTP sent to your email"}

    @staticmethod
    async def initiate_password_reset(
        db: Session,
        email: str
    ) -> Dict[str, str]:
        """Initiate password reset by sending OTP."""
        logger.info(f"Password reset requested for email: {email}")
        user = db.query(User).filter(User.email == email).first()
        if not user:
            logger.error(f"No user found for email: {email}")
            raise HTTPException(status_code=404, detail="User not found")
        
        otp = generate_otp()
        store_otp(db, user, otp)
        await send_email(
            email,
            "Password Reset OTP",
            f"Your OTP for password reset is {otp}. It expires in 10 minutes."
        )
        logger.info(f"Password reset OTP sent to: {email}")
        return {"message": "Password reset OTP sent to your email"}

    @staticmethod
    async def reset_password(
        db: Session,
        email: str,
        otp: str,
        new_password: str
    ) -> Dict[str, str]:
        """Reset user's password using OTP."""
        logger.info(f"Password reset attempt for email: {email}")
        user = db.query(User).filter(User.email == email).first()
        if not user:
            logger.error(f"No user found for email: {email}")
            raise HTTPException(status_code=404, detail="User not found")
        
        AuthHandler.validate_otp(user, otp)
        
        user.hashed_password = hash_password(new_password)
        user.otp = None
        user.otp_expiry = None
        db.commit()
        db.refresh(user)
        
        logger.info(f"Password reset successful for email: {email}")
        return {"message": "Password reset successfully"} 