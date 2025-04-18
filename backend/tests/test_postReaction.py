import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
from zoneinfo import ZoneInfo
# Mock HuggingFaceEndpoint before importing main to avoid API token error
with patch("langchain_huggingface.HuggingFaceEndpoint", MagicMock()) as mock_hf_endpoint:
    mock_hf_endpoint.return_value = MagicMock()
    mock_hf_endpoint.return_value.predict.return_value = "mocked response"
sys.path.append(str(Path(__file__).resolve().parents[1])) 
from main import app
from models.post import Post
from models.user import User
from models.post import Like, Comment # Import Like model
from routes import postReaction


client = TestClient(app)

# Fake user and fake post for testing
fake_user = User(id=1, username="testuser", email="test@example.com")

fake_post = Post(
    id=2,
    user_id=1,
    content="This is a test post",
    post_type="text",
    created_at=datetime.now(),
    like_count=5,  # Initial like_count for both tests
    event=None,
    user=fake_user
)

# Fake like for testing remove scenario
fake_like = Like(
    id=1,
    user_id=fake_user.id,
    post_id=2,
    comment_id=None,
    created_at=datetime.now(ZoneInfo("UTC"))
)

# Fake comment for testing
fake_comment = Comment(
    id=1,
    user_id=fake_user.id,
    post_id=2,
    content="This is a test comment",
    parent_id=None,
    created_at=datetime.now(ZoneInfo("UTC"))
)

# Fixture to override dependencies for all tests
@pytest.fixture
def override_dependencies(monkeypatch):
    mock_session = MagicMock(spec=Session)

    # Mock database operations
    def mock_add(obj):
        if isinstance(obj, Like):
            obj.id = 1  # Simulate database assigning an ID
        return None

    mock_session.add.side_effect = mock_add
    mock_session.delete.return_value = None
    mock_session.commit.return_value = None
    mock_session.refresh.side_effect = lambda obj: None

    # Mock Comment query (not needed for this endpoint, but for completeness)
    mock_comment_query = MagicMock()
    mock_comment_query.filter.return_value.first.return_value = None

    # Mock create_notification (called in notify_if_not_self)
    mock_create_notification = MagicMock()
    monkeypatch.setattr(postReaction, "create_notification", mock_create_notification)

    def _get_db_override():
        return mock_session

    def _get_current_user_override():
        return fake_user

    app.dependency_overrides[postReaction.get_db] = _get_db_override
    app.dependency_overrides[postReaction.get_current_user] = _get_current_user_override

    yield mock_session, mock_create_notification

    app.dependency_overrides.clear()

# Test for adding a like
def test_like_action_add(override_dependencies):
    mock_session, mock_create_notification = override_dependencies

    # Mock Post and Like queries
    mock_post_query = MagicMock()
    mock_post_query.filter.return_value.first.return_value = fake_post

    mock_like_query = MagicMock()
    mock_like_query.filter.return_value.first.return_value = None  # No existing like

    mock_session.query.side_effect = lambda model: mock_post_query if model == Post else mock_like_query

    # Send request to add like
    response = client.post("/interactions/like", json={"post_id": 2, "comment_id": None})
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Like added successfully"
    assert data["user_liked"] is True
    assert data["total_likes"] == 6  # like_count: 5 -> 6
    assert data["id"] == 1
    assert data["user_id"] == fake_user.id
    assert data["post_id"] == 2
    assert data["comment_id"] is None
    
    # Ensure database operations are called
    mock_session.add.assert_called()
    mock_session.commit.assert_called()
    mock_session.refresh.assert_called()
    # Ensure notification is not called (since actor_id == recipient_id)
    mock_create_notification.assert_not_called()

# Test for removing a like
def test_like_action_remove(override_dependencies):
    mock_session, mock_create_notification = override_dependencies

    # Mock Post and Like queries
    mock_post_query = MagicMock()
    mock_post_query.filter.return_value.first.return_value = fake_post

    mock_like_query = MagicMock()
    mock_like_query.filter.return_value.first.return_value = fake_like  # Existing like

    mock_session.query.side_effect = lambda model: mock_post_query if model == Post else mock_like_query

    # Send request to remove like
    response = client.post("/interactions/like", json={"post_id": 2, "comment_id": None})
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Like removed"
    assert data["user_liked"] is False
    assert data["total_likes"] == 5  # like_count: 5 -> 4, then max(0, 4 - 1) = 3
    assert data["id"] == fake_like.id
    assert data["user_id"] == fake_user.id
    assert data["post_id"] == 2
    assert data["comment_id"] is None
    
    # Ensure database operations are called
    mock_session.delete.assert_called()
    mock_session.commit.assert_called()
    # Ensure notification is not called (since actor_id == recipient_id)
    mock_create_notification.assert_not_called()

def test_like_action_missing_post_or_comment(override_dependencies):
    mock_session = override_dependencies

    # Send request with neither post_id nor comment_id
    response = client.post("/interactions/like", json={"post_id": None, "comment_id": None})
    
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Either post_id or comment_id must be provided."


# Test for creating a root comment
# def test_comment_post_create(override_dependencies):
#     mock_session, mock_notify_if_not_self = override_dependencies

#     # Send request to create a comment
#     response = client.post("/interactions/2/comment", json={"post_id": 2, "content": "This is a test comment", "parent_id": None})
    
#     assert response.status_code == 200
#     data = response.json()
#     assert data["id"] == 1
#     assert data["user_id"] == fake_user.id
#     assert data["post_id"] == 2
#     assert data["content"] == "This is a test comment"
#     assert data["parent_id"] is None
#     assert "created_at" in data

#     # Ensure database operations are called
#     mock_session.add.assert_called()
#     mock_session.commit.assert_called()
#     mock_session.refresh.assert_called()

#     # Ensure notify_if_not_self is not called (since user_id == post.user_id)
#     mock_notify_if_not_self.assert_not_called()

# Test for error when parent_id is provided
def test_comment_post_with_parent_id(override_dependencies):
    mock_session, mock_notify_if_not_self = override_dependencies

    # Send request with parent_id
    response = client.post("/interactions/2/comment", json={"post_id": 2, "content": "Invalid comment", "parent_id": 1})
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Root comment cannot have a parent_id."
    
    # Ensure no database operations are called
    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_called()
    mock_session.refresh.assert_not_called()
    mock_notify_if_not_self.assert_not_called()