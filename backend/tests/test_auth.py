import sys
from pathlib import Path
import pytest
import uuid
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from main import app
from database.session import SessionLocal, Base, engine
from models.user import User
from core.security import hash_password
from sqlalchemy.orm import Session

# Initialize FastAPI test client
client = TestClient(app)

# Ensure tables exist before testing
Base.metadata.create_all(bind=engine)

# Dependency override to use testing DB session
def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Override DB session dependency globally
app.dependency_overrides[Session] = override_get_db

# ----------------------
# 🔧 Fixture for test user
# ----------------------
@pytest.fixture
def test_user():
    db: Session = SessionLocal()
    user = db.query(User).filter(User.username == "testuser").first()
    if not user:
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=hash_password("testpass"),
            profile_completed=True,
            is_verified=True  # Set user as verified for testing
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    db.close()
    return user

# ----------------------
# ✅ Test user signup
# ----------------------
def test_signup():
    unique_username = f"user_{uuid.uuid4().hex[:8]}"
    unique_email = f"{unique_username}@example.com"

    response = client.post(
        "/auth/signup/",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "newpass"
        }
    )
    assert response.status_code == 200
    assert "User created successfully" in response.json()["message"]

    # Verify the user exists in DB but is not verified
    db = SessionLocal()
    user = db.query(User).filter(User.username == unique_username).first()
    assert user is not None
    assert user.is_verified is False
    assert user.otp is not None  # OTP should be set
    assert user.otp_expiry is not None  # OTP expiry should be set
    db.close()

# ----------------------
# ✅ Test login success
# ----------------------
def test_login_success(test_user):
    response = client.post(
        "/auth/token",
        data={
            "username": "testuser",
            "password": "testpass"
        }
    )
    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    assert json_data["token_type"] == "bearer"

def test_login_unverified_user():
    # Create an unverified user
    unique_username = f"unverified_{uuid.uuid4().hex[:8]}"
    unique_email = f"{unique_username}@example.com"
    db = SessionLocal()
    user = User(
        username=unique_username,
        email=unique_email,
        hashed_password=hash_password("testpass"),
        is_verified=False
    )
    db.add(user)
    db.commit()
    db.close()

    # Try to login with unverified user
    response = client.post(
        "/auth/token",
        data={
            "username": unique_username,
            "password": "testpass"
        }
    )
    assert response.status_code == 403
    assert "verify your email" in response.json()["detail"].lower()

# ----------------------
# ✅ Test fetch current user
# ----------------------
def test_get_current_user(test_user):
    token_response = client.post(
        "/auth/token",
        data={
            "username": "testuser",
            "password": "testpass"
        }
    )
    token = token_response.json()["access_token"]

    response = client.get(
        "/auth/users/me/",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    user_data = response.json()
    assert user_data["username"] == "testuser"
    assert user_data["email"] == "test@example.com"

# ----------------------
# ✅ Test OTP verification
# ----------------------
def test_verify_otp():
    # Create a new unverified user with OTP
    unique_username = f"otp_user_{uuid.uuid4().hex[:8]}"
    unique_email = f"{unique_username}@example.com"
    test_otp = "123456"  # Test OTP
    
    db = SessionLocal()
    user = User(
        username=unique_username,
        email=unique_email,
        hashed_password=hash_password("testpass"),
        is_verified=False,
        otp=test_otp,
        otp_expiry=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()

    # Test valid OTP verification
    response = client.post(
        "/auth/verify-otp/",
        json={
            "email": unique_email,
            "otp": test_otp
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "Email verified" in response.json()["message"]

    # Verify user is now verified in DB
    db = SessionLocal()
    user = db.query(User).filter(User.email == unique_email).first()
    assert user.is_verified is True
    assert user.otp is None  # OTP should be cleared after verification
    assert user.otp_expiry is None
    db.close()

def test_verify_otp_invalid():
    # Create a new unverified user with OTP
    unique_username = f"otp_user_{uuid.uuid4().hex[:8]}"
    unique_email = f"{unique_username}@example.com"
    test_otp = "123456"  # Test OTP
    
    db = SessionLocal()
    user = User(
        username=unique_username,
        email=unique_email,
        hashed_password=hash_password("testpass"),
        is_verified=False,
        otp=test_otp,
        otp_expiry=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(user)
    db.commit()
    db.close()

    # Test invalid OTP
    response = client.post(
        "/auth/verify-otp/",
        json={
            "email": unique_email,
            "otp": "wrong_otp"
        }
    )
    assert response.status_code == 400
    assert "Invalid OTP" in response.json()["detail"]

def test_verify_otp_expired():
    # Create a new unverified user with expired OTP
    unique_username = f"otp_user_{uuid.uuid4().hex[:8]}"
    unique_email = f"{unique_username}@example.com"
    test_otp = "123456"  # Test OTP
    
    db = SessionLocal()
    user = User(
        username=unique_username,
        email=unique_email,
        hashed_password=hash_password("testpass"),
        is_verified=False,
        otp=test_otp,
        otp_expiry=datetime.utcnow() - timedelta(minutes=1)  # Expired OTP
    )
    db.add(user)
    db.commit()
    db.close()

    # Test expired OTP
    response = client.post(
        "/auth/verify-otp/",
        json={
            "email": unique_email,
            "otp": test_otp
        }
    )
    assert response.status_code == 400
    assert "OTP expired" in response.json()["detail"]
