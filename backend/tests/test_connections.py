import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path
import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from fastapi import HTTPException

# Load env variables for token creation
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "testsecretkey")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

sys.path.append(str(Path(__file__).resolve().parents[1]))

from main import app
from models.user import User
from models.connection import Connection, ConnectionStatus
from api.v1.endpoints import connections
from api.v1.endpoints.auth import oauth2_scheme, get_current_user

# Ensure routes are registered correctly for testing
app.include_router(connections.router, prefix="/connections", tags=["Connections"])

# Create test client
client = TestClient(app)

# Mock users
fake_user1 = User(
    id=1,
    username="user1",
    email="user1@example.com",
    profile_picture="user1.jpg",
    is_verified=True,
    profile_completed=True
)

fake_user2 = User(
    id=2,
    username="user2",
    email="user2@example.com",
    profile_picture="user2.jpg",
    is_verified=True,
    profile_completed=True
)

fake_user3 = User(
    id=3,
    username="user3",
    email="user3@example.com",
    profile_picture="user3.jpg",
    is_verified=True,
    profile_completed=True
)

# Mock connections
fake_pending_connection = Connection(
    id=1,
    user_id=1,
    friend_id=2,
    status=ConnectionStatus.PENDING
)

fake_accepted_connection = Connection(
    id=2,
    user_id=1,
    friend_id=3,
    status=ConnectionStatus.ACCEPTED
)

# Create a mock token for authentication
def create_test_token():
    expire = datetime.utcnow() + timedelta(minutes=15)
    payload = {
        "sub": fake_user1.username,
        "exp": expire
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

# Override the oauth2_scheme dependency
def get_test_token():
    return create_test_token()

# Override the get_current_user dependency
def get_test_user():
    return fake_user1

@pytest.fixture
def override_dependencies(monkeypatch):
    # Create mocks
    mock_session = MagicMock(spec=Session)
    mock_connection_handler = MagicMock()
    
    # Mock connection handler methods
    mock_connection_handler.send_connection_request.return_value = fake_pending_connection
    mock_connection_handler.accept_connection_request.return_value = {"message": "Connection accepted!"}
    mock_connection_handler.reject_connection_request.return_value = {"message": "Connection request rejected"}
    mock_connection_handler.get_user_connections.return_value = [
        {
            "connection_id": fake_accepted_connection.id,
            "friend_id": fake_user3.id,
            "username": fake_user3.username,
            "email": fake_user3.email,
            "profile_picture": fake_user3.profile_picture
        }
    ]
    mock_connection_handler.get_pending_requests.return_value = [
        {
            "request_id": fake_pending_connection.id,
            "sender_id": fake_user1.id,
            "username": fake_user1.username,
            "email": fake_user1.email,
            "profile_picture": fake_user1.profile_picture
        }
    ]
    mock_connection_handler.get_available_users.return_value = [
        {
            "user_id": fake_user2.id,
            "username": fake_user2.username,
            "email": fake_user2.email,
            "profile_picture": fake_user2.profile_picture
        }
    ]
    mock_connection_handler.get_user_by_id.return_value = {
        "user_id": fake_user2.id,
        "username": fake_user2.username,
        "email": fake_user2.email,
        "profile_picture": fake_user2.profile_picture
    }
    
    # Replace ConnectionHandler with mock
    monkeypatch.setattr(connections, "ConnectionHandler", mock_connection_handler)
    
    # Mock get_current_user to bypass authentication
    app.dependency_overrides[get_current_user] = get_test_user
    app.dependency_overrides[oauth2_scheme] = get_test_token
    app.dependency_overrides[connections.get_db] = lambda: mock_session
    
    # Setup test token header for authentication
    global test_token
    test_token = create_test_token()
    
    mocks = {
        "session": mock_session,
        "connection_handler": mock_connection_handler,
        "token": test_token
    }
    
    yield mocks
    
    app.dependency_overrides.clear()

def test_send_connection(override_dependencies):
    mocks = override_dependencies
    connection_handler = mocks["connection_handler"]
    
    # Test data
    request_data = {"friend_id": 2}
    
    # Send connection request
    response = client.post(
        "/connections/connect/", 
        json=request_data,
        headers={"Authorization": f"Bearer {mocks['token']}"}
    )
    
    # Assertions
    assert response.status_code == 200
    connection = response.json()
    assert connection["id"] == fake_pending_connection.id
    assert connection["user_id"] == fake_user1.id
    assert connection["friend_id"] == fake_user2.id
    assert connection["status"] == ConnectionStatus.PENDING
    
    # Verify ConnectionHandler method called
    connection_handler.send_connection_request.assert_called_once_with(
        db=mocks["session"],
        user_id=fake_user1.id,
        friend_id=request_data["friend_id"]
    )

def test_accept_connection(override_dependencies):
    mocks = override_dependencies
    connection_handler = mocks["connection_handler"]
    
    # Accept connection request
    response = client.post(
        f"/connections/accept/{fake_pending_connection.id}",
        headers={"Authorization": f"Bearer {mocks['token']}"}
    )
    
    # Assertions
    assert response.status_code == 200
    result = response.json()
    assert result["message"] == "Connection accepted!"
    
    # Verify ConnectionHandler method called
    connection_handler.accept_connection_request.assert_called_once_with(
        db=mocks["session"],
        request_id=fake_pending_connection.id,
        user_id=fake_user1.id
    )

def test_reject_connection(override_dependencies):
    mocks = override_dependencies
    connection_handler = mocks["connection_handler"]
    
    # Reject connection request
    response = client.post(
        f"/connections/reject/{fake_pending_connection.id}",
        headers={"Authorization": f"Bearer {mocks['token']}"}
    )
    
    # Assertions
    assert response.status_code == 200
    result = response.json()
    assert result["message"] == "Connection request rejected"
    
    # Verify ConnectionHandler method called
    connection_handler.reject_connection_request.assert_called_once_with(
        db=mocks["session"],
        request_id=fake_pending_connection.id,
        user_id=fake_user1.id
    )

def test_list_connections(override_dependencies):
    mocks = override_dependencies
    connection_handler = mocks["connection_handler"]
    
    # Get user connections
    response = client.get(
        "/connections/connections",
        headers={"Authorization": f"Bearer {mocks['token']}"}
    )
    
    # Assertions
    assert response.status_code == 200
    connections = response.json()
    assert len(connections) == 1
    assert connections[0]["connection_id"] == fake_accepted_connection.id
    assert connections[0]["friend_id"] == fake_user3.id
    assert connections[0]["username"] == fake_user3.username
    
    # Verify ConnectionHandler method called
    connection_handler.get_user_connections.assert_called_once_with(
        db=mocks["session"],
        user_id=fake_user1.id
    )

def test_get_users(override_dependencies):
    mocks = override_dependencies
    connection_handler = mocks["connection_handler"]
    
    # Get available users
    response = client.get(
        "/connections/users",
        headers={"Authorization": f"Bearer {mocks['token']}"}
    )
    
    # Assertions
    assert response.status_code == 200
    users = response.json()
    assert len(users) == 1
    assert users[0]["user_id"] == fake_user2.id
    assert users[0]["username"] == fake_user2.username
    
    # Verify ConnectionHandler method called
    connection_handler.get_available_users.assert_called_once_with(
        db=mocks["session"],
        current_user_id=fake_user1.id
    )

def test_get_pending_requests(override_dependencies):
    mocks = override_dependencies
    connection_handler = mocks["connection_handler"]
    
    # Get pending requests
    response = client.get(
        "/connections/pending",
        headers={"Authorization": f"Bearer {mocks['token']}"}
    )
    
    # Assertions
    assert response.status_code == 200
    requests = response.json()
    assert len(requests) == 1
    assert requests[0]["request_id"] == fake_pending_connection.id
    assert requests[0]["sender_id"] == fake_user1.id
    assert requests[0]["username"] == fake_user1.username
    
    # Verify ConnectionHandler method called
    connection_handler.get_pending_requests.assert_called_once_with(
        db=mocks["session"],
        user_id=fake_user1.id
    )

def test_get_user(override_dependencies):
    mocks = override_dependencies
    connection_handler = mocks["connection_handler"]
    
    # Get specific user
    response = client.get(
        f"/connections/user/{fake_user2.id}",
        headers={"Authorization": f"Bearer {mocks['token']}"}
    )
    
    # Assertions
    assert response.status_code == 200
    user = response.json()
    assert user["user_id"] == fake_user2.id
    assert user["username"] == fake_user2.username
    assert user["email"] == fake_user2.email
    
    # Verify ConnectionHandler method called
    connection_handler.get_user_by_id.assert_called_once_with(
        db=mocks["session"],
        user_id=fake_user2.id
    )

def test_connection_error_handling(override_dependencies):
    mocks = override_dependencies
    connection_handler = mocks["connection_handler"]
    
    # Mock ConnectionHandler to raise an HTTPException instead of a generic Exception
    connection_handler.send_connection_request.side_effect = HTTPException(
        status_code=400, 
        detail="Test error"
    )
    
    # Send connection request that will cause an error
    response = client.post(
        "/connections/connect/", 
        json={"friend_id": 999},
        headers={"Authorization": f"Bearer {mocks['token']}"}
    )
    
    # Assertions
    assert response.status_code == 400
    assert response.json()["detail"] == "Test error"
