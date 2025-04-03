# F:\LearnaThon\noobsquad\backend\tests\test_connections.py
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models.user import User
from models.connection import Connection
from core.security import hash_password

sys.path.append(str(Path(__file__).resolve().parents[1]))
from main import app

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

@pytest.fixture
def friend_user(db_session: Session):
    user = db_session.query(User).filter(User.username == "frienduser").first()
    if not user:
        user = User(
            username="frienduser",
            email="friend@example.com",
            hashed_password=hash_password("friendpass"),
            profile_completed=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user

@pytest.fixture
def jwt_token(test_user: User, client: TestClient):
    response = client.post(
        "/auth/token",
        data={"username": test_user.username, "password": "testpass"}
    )
    return response.json().get("access_token")

def test_accept_connection(test_user: User, friend_user: User, db_session: Session, client: TestClient, jwt_token: str):
    with db_session.begin():  # Use transaction scope
        connection = Connection(user_id=test_user.id, friend_id=friend_user.id, status="pending")
        db_session.add(connection)
        db_session.commit()
        db_session.refresh(connection)
    
    response = client.post(
        f"/connections/accept/{connection.id}",
        headers={"Authorization": f"Bearer {jwt_token}"}
    )
    assert response.status_code == 200
    assert "Connection accepted!" in response.json()["message"]

# Apply similar transaction scope to other tests
def test_reject_connection(test_user: User, friend_user: User, db_session: Session, client: TestClient, jwt_token: str):
    with db_session.begin():
        connection = Connection(user_id=test_user.id, friend_id=friend_user.id, status="pending")
        db_session.add(connection)
        db_session.commit()
        db_session.refresh(connection)
    
    response = client.post(
        f"/connections/reject/{connection.id}",
        headers={"Authorization": f"Bearer {jwt_token}"}
    )
    assert response.status_code == 200
    assert "Connection rejected!" in response.json()["message"]

def test_list_connections(test_user: User, friend_user: User, db_session: Session, client: TestClient, jwt_token: str):
    with db_session.begin():
        connection = Connection(user_id=test_user.id, friend_id=friend_user.id, status="accepted")
        db_session.add(connection)
        db_session.commit()
    
    response = client.get(
        "/connections/connections",
        headers={"Authorization": f"Bearer {jwt_token}"}
    )
    assert response.status_code == 200
    connections = response.json()
    assert len(connections) > 0

def test_get_users(test_user: User, friend_user: User, db_session: Session, client: TestClient, jwt_token: str):
    with db_session.begin():
        connection = Connection(user_id=test_user.id, friend_id=friend_user.id, status="accepted")
        db_session.add(connection)
        db_session.commit()
    
    response = client.get(
        "/connections/users",
        headers={"Authorization": f"Bearer {jwt_token}"}
    )
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 0

def test_get_user(test_user: User, friend_user: User, client: TestClient, jwt_token: str):
    response = client.get(
        f"/connections/user/{friend_user.id}",
        headers={"Authorization": f"Bearer {jwt_token}"}
    )
    assert response.status_code == 200
    user = response.json()
    assert user["username"] == "frienduser"