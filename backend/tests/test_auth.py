# F:\LearnaThon\noobsquad\backend\tests\test_auth.py
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
sys.path.append(str(Path(__file__).resolve().parents[1]))

from main import app
from models.user import User
from core.security import hash_password

@pytest.fixture
def test_user(db_session: Session):
    user = db_session.query(User).filter(User.username == "testuser").first()
    if not user:
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=hash_password("testpass"),
            profile_completed=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user

def test_signup(client: TestClient):
    response = client.post(
        "/auth/signup/",
        json={
            "username": "testuser_signup",
            "email": "signup@example.com",
            "password": "newpass"
        }
    )
    assert response.status_code == 200
    assert "User created successfully" in response.json()["message"]