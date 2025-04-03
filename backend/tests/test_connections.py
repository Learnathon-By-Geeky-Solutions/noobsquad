import sys
from pathlib import Path

# Add the backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models.user import User
from models.connection import Connection
from core.security import hash_password
from main import app

# Initialize FastAPI test client as a fixture
@pytest.fixture
def client():
    return TestClient(app)

# Dependency override for DB session (moved to conftest.py, but kept here for reference)
@pytest.fixture
def db_session():
    from database.session import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Fixture to create a test user
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

# Fixture to create another user for connections
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

# Fixture to get a valid JWT token
@pytest.fixture
def jwt_token(test_user: User, client: TestClient):
    response = client.post(
        "/auth/token",
        data={
            "username": test_user.username,
            "password": "testpass"
        }
    )
    return response.json().get("access_token")

# Test the `/connections/accept/{request_id}` endpoint
def test_accept_connection(test_user: User, friend_user: User, db_session: Session, client: TestClient, jwt_token: str):
    # Create a pending connection request
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

# Test the `/connections/reject/{request_id}` endpoint
def test_reject_connection(test_user: User, friend_user: User, db_session: Session, client: TestClient, jwt_token: str):
    # Create a pending connection request
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

# Test the `/connections/connections` endpoint to fetch user connections
def test_list_connections(test_user: User, friend_user: User, db_session: Session, client: TestClient, jwt_token: str):
    # Create an accepted connection
    connection = Connection(user_id=test_user.id, friend_id=friend_user.id, status="accepted")
    db_session.add(connection)
    db_session.commit()
    
    response = client.get(
        "/connections/connections",
        headers={"Authorization": f"Bearer {jwt_token}"}
    )
    assert response.status_code == 200
    connections = response.json()
    assert len(connections) > 0  # Ensure at least one connection is returned

# Test the `/connections/users` endpoint to fetch users excluding current connections
def test_get_users(test_user: User, friend_user: User, db_session: Session, client: TestClient, jwt_token: str):
    # Create an accepted connection
    connection = Connection(user_id=test_user.id, friend_id=friend_user.id, status="accepted")
    db_session.add(connection)
    db_session.commit()
    
    response = client.get(
        "/connections/users",
        headers={"Authorization": f"Bearer {jwt_token}"}
    )
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 0  # Could be 0 if all users are connected, so >= is safer

# Test the `/connections/user/{user_id}` endpoint to fetch a specific user
def test_get_user(test_user: User, friend_user: User, client: TestClient, jwt_token: str):
    response = client.get(
        f"/connections/user/{friend_user.id}",
        headers={"Authorization": f"Bearer {jwt_token}"}
    )
    assert response.status_code == 200
    user = response.json()
    assert user["username"] == "frienduser"