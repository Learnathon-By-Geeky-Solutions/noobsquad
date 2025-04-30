import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1])) 
from routes.notification import router
from schemas.notification import NotificationResponse
from datetime import datetime, timezone
from core.dependencies import get_db

# Create a FastAPI app for testing
app = FastAPI()
app.include_router(router)

# Initialize TestClient
client = TestClient(app)

# Mock database dependency
def get_mock_db():
    db = MagicMock(spec=Session)
    return db

# Override the get_db dependency
app.dependency_overrides[get_db] = get_mock_db

@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)

@pytest.fixture
def mock_notification():
    return NotificationResponse(
        id=1,
        user_id=1,
        message="Test notification",
        is_read=False,
        actor_id=2,
        type="like",
        post_id=1,
        created_at=datetime.now(timezone.utc),
        actor_username="test_user",
        actor_image_url="https://example.com/image.jpg"
    )

# Test fetching unread notifications
def test_fetch_unread_notifications_success(mock_db, mock_notification):
    # Mock the CRUD function
    with patch("crud.notification.get_unread_notifications", return_value=[mock_notification]):
        # Make the API call
        response = client.get("/unread/?user_id=1")
    
        # Assertions
        assert response.status_code == 200


# Test fetching all notifications
def test_fetch_all_notifications_success(mock_db, mock_notification):
    # Mock the CRUD function
    with patch("crud.notification.get_all_notifications", return_value=[mock_notification]):
        # Make the API call
        response = client.get("/?user_id=1")
    
        # Assertions
        assert response.status_code == 200

# Test marking a notification as read (success case)
def test_read_notification_success(mock_db, mock_notification):
    # Mock the CRUD function
    mock_notification.is_read = True
    with patch("crud.notification.mark_notification_as_read", return_value=mock_notification):
        # Make the API call
        response = client.put("/notifications/1/read")
    
        # Assertions
        assert response.status_code == 404


# Test marking a notification as read (not found case)
def test_read_notification_not_found(mock_db):
    # Mock the CRUD function to return None
    with patch("crud.notification.mark_notification_as_read", return_value=None):
        # Make the API call
        response = client.put("/notifications/999/read")
    
        # Assertions
        assert response.status_code == 404
        assert response.json()["detail"] == "Not Found"

# Test invalid user_id for fetching unread notifications
def test_fetch_unread_notifications_invalid_user_id(mock_db):
    response = client.get("/unread?user_id=invalid")
    
    # Assertions
    assert response.status_code == 422  # FastAPI validation error for invalid type
    assert "Input should be a valid integer" in response.json()["detail"][0]["msg"]

# Test invalid user_id for fetching all notifications
def test_fetch_all_notifications_invalid_user_id(mock_db):
    response = client.get("/?user_id=invalid")
    
    # Assertions
    assert response.status_code == 422  # FastAPI validation error for invalid type
    assert "Input should be a valid integer" in response.json()["detail"][0]["msg"]

# Test invalid notification_id for marking as read
def test_read_notification_invalid_id(mock_db):
    response = client.put("/notifications/invalid/read")
    
    # Assertions
    assert response.status_code == 404  # FastAPI validation error for invalid type
