import sys
from pathlib import Path
import pytest
import uuid
from fastapi.testclient import TestClient

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
            profile_completed=True
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
