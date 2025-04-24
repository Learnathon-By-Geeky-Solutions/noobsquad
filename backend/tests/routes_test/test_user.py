import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

# Add the backend directory to the path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from main import app
from models.user import User
from schemas.user import UserResponse
from routes.user import get_db

# Create test client
client = TestClient(app)

# Test user data
test_user = User(
    id=1,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed_password_for_testing",
    is_active=True,
    is_verified=True,
    profile_picture="test_pic.jpg",
    university_name="Test University",
    department="Computer Science",
    fields_of_interest="AI, Machine Learning, Python",
    profile_completed=True
)

# Fixture to override dependencies
@pytest.fixture(autouse=True)
def override_dependencies(monkeypatch):
    mock_session = MagicMock(spec=Session)
    
    def _get_db_override():
        return mock_session
    
    app.dependency_overrides[get_db] = _get_db_override
    
    yield mock_session
    
    app.dependency_overrides.clear()

# Test get_user_by_username route - successful retrieval
def test_get_user_by_username_success(override_dependencies):
    mock_session = override_dependencies
    
    # Configure mock to return our test user
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = test_user
    mock_session.query.return_value = mock_query
    
    # Make request to the endpoint
    response = client.get("/user/username/testuser")
    
    # Assertions
    assert response.status_code == 200
    assert response.json() == 1  # Should return the user ID
    
    # Verify the query was made correctly
    mock_session.query.assert_called_once_with(User)
    mock_query.filter.assert_called_once()

# Test get_user_by_username route - user not found
def test_get_user_by_username_not_found(override_dependencies):
    mock_session = override_dependencies
    
    # Configure mock to return None (user not found)
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = None
    mock_session.query.return_value = mock_query
    
    # Make request to the endpoint
    response = client.get("/user/username/nonexistent")
    
    # Assertions
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

# Test get_user_profile route - successful retrieval
def test_get_user_profile_success(override_dependencies):
    mock_session = override_dependencies
    
    # Configure mock to return our test user
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = test_user
    mock_session.query.return_value = mock_query
    
    # Make request to the endpoint
    response = client.get("/user/profile/1")
    
    # Assertions
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["id"] == 1
    assert user_data["username"] == "testuser"
    assert user_data["email"] == "test@example.com"
    assert user_data["profile_picture"] == "test_pic.jpg"
    assert user_data["university_name"] == "Test University"
    assert user_data["department"] == "Computer Science"
    assert user_data["fields_of_interest"] == "AI, Machine Learning, Python"
    assert user_data["profile_completed"] is True
    
    # Verify the query was made correctly
    mock_session.query.assert_called_once_with(User)
    mock_query.filter.assert_called_once()

# Test get_user_profile route - user not found
def test_get_user_profile_not_found(override_dependencies):
    mock_session = override_dependencies
    
    # Configure mock to return None (user not found)
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = None
    mock_session.query.return_value = mock_query
    
    # Make request to the endpoint
    response = client.get("/user/profile/999")
    
    # Assertions
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

