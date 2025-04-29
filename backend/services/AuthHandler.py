from datetime import datetime, timezone
from typing import Dict
from fastapi import HTTPException
from sqlalchemy.orm import Session
import jwt
from models.user import User
from core.security import hash_password, verify_password, create_access_token, generate_otp, store_otp
from core.email import send_email
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


class AuthHandler:
    @staticmethod
    def _get_user_by_username_or_email(db: Session, username_or_email: str) -> User:
        return db.query(User).filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

    @staticmethod
    def _get_user_by_email(db: Session, email: str) -> User:
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def _get_user_by_username(db: Session, username: str) -> User:
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def _check_otp_validity(user: User, otp: str):
        if user.otp != otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")
        if not user.otp_expiry or user.otp_expiry < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="OTP expired")

    @staticmethod
    async def _send_otp_email(email: str, subject: str, otp: str):
        await send_email(email, subject, f"Your OTP is {otp}")

    @staticmethod
    async def create_user(db: Session, username: str, email: str, password: str) -> Dict[str, str]:
        """Create a new user and send verification OTP."""
        if AuthHandler._get_user_by_username(db, username):
            raise HTTPException(status_code=400, detail="Username already taken")

        new_user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            profile_completed=False,
            is_verified=False
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        otp = generate_otp()
        store_otp(db, new_user, otp)
        await AuthHandler._send_otp_email(email, "Verify Your Email", otp)

        return {"message": "User created successfully. Please verify your email."}

    @staticmethod
    async def authenticate_user(db: Session, username_or_email: str, password: str) -> Dict[str, str]:
        """Authenticate user and return access token."""
        user = AuthHandler._get_user_by_username_or_email(db, username_or_email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not user.is_verified:
            raise HTTPException(status_code=403, detail="Please verify your email")

        return {
            "access_token": create_access_token({"sub": user.username}),
            "token_type": "bearer"
        }

    @staticmethod
    def get_current_user(db: Session, token: str) -> User:
        """Get current user from JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if not username:
                raise HTTPException(status_code=401, detail="Invalid token")
            user = AuthHandler._get_user_by_username(db, username)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return user
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

    @staticmethod
    async def verify_email(db: Session, email: str, otp: str) -> Dict[str, str]:
        """Verify user's email with OTP."""
        user = AuthHandler._get_user_by_email(db, email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user.is_verified:
            raise HTTPException(status_code=400, detail="Email already verified")

        AuthHandler._check_otp_validity(user, otp)

        user.is_verified = True
        user.otp = None
        user.otp_expiry = None
        db.commit()

        return {
            "access_token": create_access_token({"sub": user.username}),
            "token_type": "bearer",
            "message": "Email verified"
        }

    @staticmethod
    async def resend_verification_otp(db: Session, email: str) -> Dict[str, str]:
        """Resend verification OTP to user's email."""
        user = AuthHandler._get_user_by_email(db, email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user.is_verified:
            raise HTTPException(status_code=400, detail="Email already verified")

        otp = generate_otp()
        store_otp(db, user, otp)
        await AuthHandler._send_otp_email(email, "New Verification OTP", otp)

        return {"message": "New OTP sent to your email"}

    @staticmethod
    async def initiate_password_reset(db: Session, email: str) -> Dict[str, str]:
        """Initiate password reset by sending OTP."""
        user = AuthHandler._get_user_by_email(db, email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        otp = generate_otp()
        store_otp(db, user, otp)
        await AuthHandler._send_otp_email(email, "Password Reset OTP", otp)

        return {"message": "Password reset OTP sent to your email"}

    @staticmethod
    async def reset_password(db: Session, email: str, otp: str, new_password: str) -> Dict[str, str]:
        """Reset user's password using OTP."""
        user = AuthHandler._get_user_by_email(db, email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        AuthHandler._check_otp_validity(user, otp)

        user.hashed_password = hash_password(new_password)
        user.otp = None
        user.otp_expiry = None
        db.commit()

        return {"message": "Password reset successfully"}
