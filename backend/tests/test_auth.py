import pytest
from fastapi.testclient import TestClient
from main import app
from database.session import SessionLocal, Base, engine
from models.user import User
from core.security import hash_password
from sqlalchemy.orm import Session
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app


# Setup DB and client
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

app.dependency_overrides[Session] = override_get_db


@pytest.fixture
def test_user():
    db: Session = SessionLocal()
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


def test_signup():
    response = client.post(
        "/auth/signup/",
        json={"username": "newuser", "email": "newuser@example.com", "password": "newpass"}
    )
    assert response.status_code == 200
    assert "User created successfully" in response.json()["message"]


def test_login_success(test_user):
    response = client.post(
        "/auth/token",
        data={"username": "testuser", "password": "testpass"}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    assert json_data["token_type"] == "bearer"


def test_get_current_user(test_user):
    # First login to get token
    token_res = client.post(
        "/auth/token",
        data={"username": "testuser", "password": "testpass"}
    )
    access_token = token_res.json()["access_token"]

    # Now use the token to get current user
    response = client.get(
        "/auth/users/me/",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["username"] == "testuser"
    assert user_data["email"] == "test@example.com"
