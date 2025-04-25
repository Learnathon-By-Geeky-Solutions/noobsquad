import sys
from pathlib import Path
import pytest
import json
import os
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone
from io import BytesIO

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from main import app
from models.user import User
from models.chat import Message
from schemas.chat import MessageType
from core.security import hash_password
from database.session import SessionLocal
from sqlalchemy.orm import Session
from api.v1.endpoints.auth import get_current_user

# Initialize test client
client = TestClient(app)

# ----------------------
# 🔧 Test Fixtures
# ----------------------
@pytest.fixture
def test_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def test_users(test_db):
    # Create test users
    user1 = test_db.query(User).filter(User.username == "chat_user1").first()
    user2 = test_db.query(User).filter(User.username == "chat_user2").first()
    
    if not user1:
        user1 = User(
            username="chat_user1",
            email="chat_user1@example.com",
            hashed_password=hash_password("testpass"),
            is_verified=True
        )
        test_db.add(user1)
    
    if not user2:
        user2 = User(
            username="chat_user2",
            email="chat_user2@example.com",
            hashed_password=hash_password("testpass"),
            is_verified=True
        )
        test_db.add(user2)
    
    test_db.commit()
    
    if not user1.id:
        test_db.refresh(user1)
    if not user2.id:
        test_db.refresh(user2)
    
    return user1, user2

@pytest.fixture
def test_messages(test_db, test_users):
    user1, user2 = test_users
    
    # Clean any existing test messages
    test_db.query(Message).filter(
        (Message.sender_id == user1.id) | (Message.receiver_id == user1.id)
    ).delete()
    test_db.commit()
    
    # Create test messages
    messages = [
        Message(
            sender_id=user1.id,
            receiver_id=user2.id,
            content="Hello from user1",
            message_type="text",
            timestamp=datetime.now(timezone.utc),
            is_read=True
        ),
        Message(
            sender_id=user2.id,
            receiver_id=user1.id,
            content="Hello from user2",
            message_type="text",
            timestamp=datetime.now(timezone.utc),
            is_read=False
        ),
        Message(
            sender_id=user1.id,
            receiver_id=user2.id,
            content="How are you?",
            message_type="text",
            timestamp=datetime.now(timezone.utc),
            is_read=True
        )
    ]
    
    for msg in messages:
        test_db.add(msg)
    
    test_db.commit()
    for msg in messages:
        test_db.refresh(msg)
    
    return messages

# ----------------------
# ✅ Chat History Tests
# ----------------------
def test_get_chat_history(test_db, test_users, test_messages):
    user1, user2 = test_users
    
    # Mock authentication
    def mock_current_user():
        return user1
    
    app.dependency_overrides[get_current_user] = mock_current_user
    
    # Get chat history - fix the endpoint path
    response = client.get(f"/chat/chat/history/{user2.id}")
    
    # Clean up
    app.dependency_overrides.clear()
    
    # Assertions
    assert response.status_code == 200
    messages = response.json()
    assert len(messages) == 3
    assert messages[0]["content"] == "Hello from user1"
    assert messages[1]["content"] == "Hello from user2"
    assert messages[2]["content"] == "How are you?"
    
    # Verify unread messages were marked as read
    unread_count = test_db.query(Message).filter(
        Message.sender_id == user2.id,
        Message.receiver_id == user1.id,
        Message.is_read == False
    ).count()
    assert unread_count == 0

def test_get_chat_history_unauthorized():
    # Don't set current_user override
    response = client.get(f"/chat/chat/history/2")
    assert response.status_code == 401  # Unauthorized

# ----------------------
# ✅ Conversations Tests
# ----------------------
def test_get_conversations(test_db, test_users, test_messages):
    user1, user2 = test_users
    
    # Mock authentication
    def mock_current_user():
        return user1
    
    app.dependency_overrides[get_current_user] = mock_current_user
    
    # Get conversations - fix the endpoint path
    response = client.get("/chat/chat/conversations")
    
    # Clean up
    app.dependency_overrides.clear()
    
    # Assertions
    assert response.status_code == 200
    conversations = response.json()
    assert len(conversations) == 1  # Only one conversation (with user2)
    assert conversations[0]["username"] == "chat_user2"
    assert conversations[0]["last_message"] in ["Hello from user1", "Hello from user2", "How are you?"]
    assert conversations[0]["unread_count"] >= 0

def test_get_conversations_unauthorized():
    # Don't set current_user override
    response = client.get("/chat/chat/conversations")
    assert response.status_code == 401  # Unauthorized

# ----------------------
# ✅ File Upload Tests
# ----------------------
def test_upload_file(test_db, test_users):
    user1, _ = test_users
    
    # Mock authentication
    def mock_current_user():
        return user1
    
    app.dependency_overrides[get_current_user] = mock_current_user
    
    # Create a test file
    file_content = b"test file content"
    test_file = BytesIO(file_content)
    
    # Upload file - fix the endpoint path
    response = client.post(
        "/chat/upload",
        files={"file": ("test_file.jpg", test_file, "image/jpeg")}
    )
    
    # Clean up
    app.dependency_overrides.clear()
    
    # Assertions
    assert response.status_code == 200
    assert "file_url" in response.json()
    file_url = response.json()["file_url"]
    assert file_url.startswith("/uploads/chat/")
    assert file_url.endswith(".jpg")
    
    # Clean up uploaded file
    if os.path.exists("." + file_url):
        os.remove("." + file_url)

def test_upload_invalid_file_type(test_db, test_users):
    user1, _ = test_users
    
    # Mock authentication
    def mock_current_user():
        return user1
    
    app.dependency_overrides[get_current_user] = mock_current_user
    
    # Create a test file with invalid extension
    file_content = b"test file content"
    test_file = BytesIO(file_content)
    
    # Upload file - fix the endpoint path
    response = client.post(
        "/chat/upload",
        files={"file": ("test_file.exe", test_file, "application/octet-stream")}
    )
    
    # Clean up
    app.dependency_overrides.clear()
    
    # Assertions
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]

def test_upload_file_unauthorized():
    # Don't set current_user override
    file_content = b"test file content"
    test_file = BytesIO(file_content)
    
    # Upload file without authentication - fix the endpoint path
    response = client.post(
        "/chat/upload",
        files={"file": ("test_file.jpg", test_file, "image/jpeg")}
    )
    
    assert response.status_code == 401  # Unauthorized

# ----------------------
# ✅ WebSocket Tests
# ----------------------
@pytest.mark.asyncio
async def test_websocket_endpoint():
    # This requires more complex setup with websocket testing
    # Using a simplified approach with mocks
    
    # Mock WebSocket
    mock_websocket = AsyncMock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.receive_text = AsyncMock(return_value=json.dumps({
        "receiver_id": 2,
        "content": "Test message",
        "message_type": "text"
    }))
    mock_websocket.send_text = AsyncMock()
    
    # Mock DB session
    mock_db = MagicMock()
    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()
    
    # Import the websocket_endpoint function
    from api.v1.endpoints.chat import websocket_endpoint, clients
    
    # Run the websocket handler with a disconnect after handling one message
    mock_websocket.receive_text.side_effect = [
        json.dumps({
            "receiver_id": 2,
            "content": "Test message",
            "message_type": "text"
        }),
        Exception("WebSocketDisconnect")  # Simulate disconnect after first message
    ]
    
    # Call the endpoint (will error out with WebSocketDisconnect after first message)
    with pytest.raises(Exception):
        await websocket_endpoint(mock_websocket, 1, mock_db)
    
    # Assertions
    mock_websocket.accept.assert_called_once()
    assert 1 in clients  # User should be added to clients
    mock_db.add.assert_called_once()  # Message should be added to DB
    mock_db.commit.assert_called_once()  # Changes should be committed
    
    # Cleanup
    if 1 in clients:
        del clients[1]