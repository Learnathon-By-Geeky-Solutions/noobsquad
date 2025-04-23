import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
from unittest.mock import MagicMock
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from main import app
from models.chat import Message
from models.user import User
from api.v1.endpoints import chat

# Create test client
client = TestClient(app)

# Fake user and fake friend for testing
fake_user = User(id=1, username="testuser", email="test@example.com")
fake_friend = User(id=2, username="frienduser", email="friend@example.com")

fake_message = Message(
    id=1,
    sender_id=1,
    receiver_id=2,
    content="Hello, friend!",
    timestamp=datetime.now(),
    is_read=False,
    sender=fake_user
)

# Fixture to override dependencies for all tests
@pytest.fixture(autouse=True)
def override_dependencies(monkeypatch):
    mock_session = MagicMock(spec=Session)

    def _get_db_override():
        return mock_session

    def _get_current_user_override():
        return fake_user

    app.dependency_overrides[chat.get_db] = _get_db_override
    app.dependency_overrides[chat.get_current_user] = _get_current_user_override

    yield mock_session

    app.dependency_overrides.clear()

# Test when messages are fetched for the chat history
# def test_get_chat_history(override_dependencies):
#     mock_session = override_dependencies

#     # Mock the query chain to return a list of messages
#     mock_query = MagicMock()
#     mock_query.filter.return_value.order_by.return_value.all.return_value = [fake_message]
    
#     # Mock the update of is_read status
#     mock_updated_message = MagicMock()
#     mock_updated_message.is_read = True
#     mock_query.filter.return_value.first.return_value = mock_updated_message
#     mock_session.query.return_value = mock_query

#     # Send the GET request to fetch chat history for friend with id=2
#     response = client.get("/chat/chat/history/2")
#     assert response.status_code == 200
#     data = response.json()
#     assert len(data) == 1
#     assert data[0]["id"] == fake_message.id
#     assert data[0]["content"] == fake_message.content

#     # Ensure that the database's `is_read` status is updated
#     updated_message = mock_session.query(Message).filter(Message.id == fake_message.id).first()
#     assert updated_message.is_read is True

# Test when no messages are found in the chat history
def test_get_chat_history_no_messages(override_dependencies):
    mock_session = override_dependencies

    mock_query = MagicMock()
    mock_query.filter.return_value.order_by.return_value.all.return_value = []
    mock_session.query.return_value = mock_query

    # Send the GET request to fetch chat history for friend with id=2
    response = client.get("/chat/chat/history/2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0

# Test when no conversations are found for the current user
def test_get_conversations_no_conversations(override_dependencies):
    mock_session = override_dependencies

    mock_query = MagicMock()
    mock_query.options.return_value.join.return_value.order_by.return_value.all.return_value = []
    mock_session.query.return_value = mock_query

    # Send the GET request to fetch conversations
    response = client.get("/chat/chat/conversations")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0

# Test when conversations are found and unread messages count is correct
# def test_get_conversations_with_unread_count(override_dependencies):
#     mock_session = override_dependencies

#     # Mock conversation data as a list of dictionaries
#     conversation_data = [{
#         "user_id": fake_friend.id,
#         "username": fake_friend.username,
#         "last_message": fake_message.content,
#         "timestamp": fake_message.timestamp
#     }]
    
#     # Mock the conversation query to return conversation data
#     mock_conversation_query = MagicMock()
#     mock_conversation_query.options.return_value.join.return_value.order_by.return_value.all.return_value = conversation_data
    
#     # Mock the unread count query
#     mock_unread_count_query = MagicMock()
#     mock_unread_count_query.filter.return_value.scalar.return_value = 1

#     # Configure session to return appropriate query mocks
#     def query_mock(model):
#         if model == Message:
#             return mock_conversation_query
#         return mock_unread_count_query
    
#     mock_session.query.side_effect = query_mock

#     # Send the GET request to fetch conversations
#     response = client.get("/chat/chat/conversations")
#     assert response.status_code == 200
#     data = response.json()

#     assert len(data) == 1
#     assert data[0]["user_id"] == fake_friend.id
#     assert data[0]["username"] == fake_friend.username
#     assert data[0]["unread_count"] == 1

# # Test when an internal server error occurs
# def test_get_chat_history_internal_error(override_dependencies):
#     mock_session = override_dependencies

#     # Configure the mock session to raise an exception when queried
#     mock_query = MagicMock()
#     mock_query.filter.side_effect = Exception("DB Error")
#     mock_session.query.return_value = mock_query

#     # Send the GET request to fetch chat history
#     response = client.get("/chat/chat/history/5")
#     assert response.status_code == 500
#     assert response.json()["detail"] == "Internal Server Error"