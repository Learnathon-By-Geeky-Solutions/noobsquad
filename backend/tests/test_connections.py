import sys
from pathlib import Path

# Add the backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))  # Adds the root project folder to path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models.user import User
from models.connection import Connection
from core.security import hash_password
from api.v1.endpoints.connections import router
from core.dependencies import get_db
from main import app

# Initialize FastAPI test client
client = TestClient(app)

# Dependency override to use testing DB session
@pytest.fixture
def test_db_session():
    from database.session import SessionLocal
    db = SessionLocal()
    yield db
    db.close()

# Fixture to create a test user
@pytest.fixture
def test_user(test_db_session):
    user = test_db_session.query(User).filter(User.username == "testuser").first()
    if not user:
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=hash_password("testpass"),
            profile_completed=True
        )
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)
    return user

# Fixture to create another user for connections
@pytest.fixture
def friend_user(test_db_session):
    user = test_db_session.query(User).filter(User.username == "frienduser").first()
    if not user:
        user = User(
            username="frienduser",
            email="friend@example.com",
            hashed_password=hash_password("friendpass"),
            profile_completed=True
        )
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)
    return user

# Function to get a valid JWT token
def get_jwt_token(test_user):
    response = client.post(
        "/auth/token",
        data={
            "username": test_user.username,
            "password": "testpass"
        }
    )
    return response.json().get("access_token")



# Test the `/connections/accept/{request_id}` endpoint
def test_accept_connection(test_user, friend_user, test_db_session):
    # Create a connection request between users (make sure it's pending)
    connection = Connection(user_id=test_user.id, friend_id=friend_user.id, status="pending")
    test_db_session.add(connection)
    test_db_session.commit()
    test_db_session.refresh(connection)
    
    # Get a valid JWT token
    token = get_jwt_token(test_user)
    
    response = client.post(
        f"/connections/accept/{connection.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "Connection accepted!" in response.json()["message"]

# Test the `/connections/reject/{request_id}` endpoint
def test_reject_connection(test_user, friend_user, test_db_session):
    # Create a connection request between users (make sure it's pending)
    connection = Connection(user_id=test_user.id, friend_id=friend_user.id, status="pending")
    test_db_session.add(connection)
    test_db_session.commit()
    test_db_session.refresh(connection)
    
    # Get a valid JWT token
    token = get_jwt_token(test_user)
    
    response = client.post(
        f"/connections/reject/{connection.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "Connection rejected!" in response.json()["message"]

# Test the `/connections/connections` endpoint to fetch user connections
def test_list_connections(test_user, friend_user, test_db_session):
    # Create a connection between the users
    connection = Connection(user_id=test_user.id, friend_id=friend_user.id, status="accepted")
    test_db_session.add(connection)
    test_db_session.commit()
    
    # Get a valid JWT token
    token = get_jwt_token(test_user)
    
    response = client.get(
        "/connections/connections",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    connections = response.json()
    assert len(connections) > 0  # Ensure there is at least one connection

# Test the `/connections/users` endpoint to fetch users excluding current connections
def test_get_users(test_user, friend_user, test_db_session):
    # Create a connection
    connection = Connection(user_id=test_user.id, friend_id=friend_user.id, status="accepted")
    test_db_session.add(connection)
    test_db_session.commit()
    
    # Get a valid JWT token
    token = get_jwt_token(test_user)
    
    response = client.get(
        "/connections/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    users = response.json()
    assert len(users) > 0  # Ensure there are users returned



# Test the `/connections/user/{user_id}` endpoint to fetch a specific user
def test_get_user(test_user, friend_user, test_db_session):
    # Get a valid JWT token
    token = get_jwt_token(test_user)
    
    response = client.get(
        f"/connections/user/{friend_user.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    user = response.json()
    assert user["username"] == "frienduser"
