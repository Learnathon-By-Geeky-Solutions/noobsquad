import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
import sys
import io
import json

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from main import app
from models.user import User

client = TestClient(app)

# --- Fixtures ---
@pytest.fixture
def fake_user():
    return User(id=1, username="testuser", email="test@example.com")

@pytest.fixture
def override_auth_and_db(fake_user):
    mock_db = MagicMock()
    def _get_db_override():
        return mock_db
    def _get_current_user_override():
        return fake_user
    from api.v1.endpoints.auth import get_current_user
    from core.dependencies import get_db
    app.dependency_overrides[get_current_user] = _get_current_user_override
    app.dependency_overrides[get_db] = _get_db_override
    yield mock_db
    app.dependency_overrides.clear()

# --- WebSocket Endpoint ---
@pytest.mark.asyncio
async def test_websocket_endpoint_connect_and_disconnect():
    with patch("api.v1.endpoints.chat.connect_socket", new_callable=AsyncMock) as mock_connect, \
         patch("api.v1.endpoints.chat.handle_chat_message", new_callable=AsyncMock) as mock_handle, \
         patch("api.v1.endpoints.chat.disconnect_socket", new_callable=AsyncMock) as mock_disconnect:
        # Simulate WebSocket
        class DummyWebSocket:
            def __init__(self):
                self.accepted = False
                self.sent = []
                self.closed = False
                self._recv = [json.dumps({"receiver_id": 2, "content": "hi", "message_type": "text"})]
            async def accept(self):
                self.accepted = True
            async def receive_json(self):
                if self._recv:
                    return json.loads(self._recv.pop(0))
                raise Exception("disconnect")
            async def send_json(self, data):
                self.sent.append(data)
        ws = DummyWebSocket()
        # Import endpoint
        from api.v1.endpoints.chat import websocket_endpoint
        # Should raise after disconnect
        with pytest.raises(Exception):
            await websocket_endpoint(ws, 1, MagicMock())
        mock_connect.assert_awaited_once()
        mock_handle.assert_awaited()
        mock_disconnect.assert_awaited()

# --- Conversations Endpoint ---
def test_get_conversations_success(override_auth_and_db, fake_user):
    with patch("api.v1.endpoints.chat.fetch_conversations", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = [
            {"user_id": 2, "username": "friend", "avatar": None, "last_message": "hi", "file_url": None, "message_type": "text", "timestamp": "2024-01-01T00:00:00Z", "is_sender": True, "unread_count": 0}
        ]
        response = client.get("/chat/chat/conversations")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert data[0]["username"] == "friend"

def test_get_conversations_unauthorized():
    response = client.get("/chat/chat/conversations")
    assert response.status_code == 401

# --- Chat History Endpoint ---
def test_get_chat_history_success(override_auth_and_db, fake_user):
    with patch("api.v1.endpoints.chat.fetch_chat_history", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = [
            {"id": 1, "sender_id": 1, "receiver_id": 2, "content": "hi", "file_url": None, "message_type": "text", "timestamp": "2024-01-01T00:00:00Z", "is_read": True}
        ]
        response = client.get("/chat/chat/history/2")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert data[0]["content"] == "hi"

def test_get_chat_history_unauthorized():
    response = client.get("/chat/chat/history/2")
    assert response.status_code == 401

# --- Upload Endpoint ---
def test_upload_file_success(override_auth_and_db):
    with patch("api.v1.endpoints.chat.upload_file_to_supabase", new_callable=AsyncMock) as mock_upload, \
         patch("api.v1.endpoints.chat.generate_secure_filename", return_value="secure.jpg"):
        mock_upload.return_value = "https://cdn.supabase.io/chat/secure.jpg"
        file_content = b"test file content"
        test_file = io.BytesIO(file_content)
        response = client.post(
            "/chat/upload",
            files={"file": ("test_file.jpg", test_file, "image/jpeg")}
        )
        assert response.status_code == 200
        data = response.json()
        assert "file_url" in data
        assert data["file_url"].endswith(".jpg")

def test_upload_file_invalid_type(override_auth_and_db):
    with patch("api.v1.endpoints.chat.generate_secure_filename", return_value="secure.exe"), \
         patch("api.v1.endpoints.chat.upload_file_to_supabase", new_callable=AsyncMock) as mock_upload:
        # Simulate error in upload (invalid type)
        mock_upload.side_effect = Exception("Unsupported file type")
        file_content = b"test file content"
        test_file = io.BytesIO(file_content)
        response = client.post(
            "/chat/upload",
            files={"file": ("test_file.exe", test_file, "application/octet-stream")}
        )
        assert response.status_code == 500 or response.status_code == 400
        assert "detail" in response.json()

def test_upload_file_unauthorized():
    file_content = b"test file content"
    test_file = io.BytesIO(file_content)
    response = client.post(
        "/chat/upload",
        files={"file": ("test_file.jpg", test_file, "image/jpeg")}
    )
    assert response.status_code == 200
