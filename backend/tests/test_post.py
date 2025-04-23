import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

# Mock HuggingFaceEndpoint before importing main
with patch("langchain_huggingface.HuggingFaceEndpoint", MagicMock()) as mock_hf_endpoint:
    mock_hf_endpoint.return_value = MagicMock()
    mock_hf_endpoint.return_value.predict.return_value = "mocked response"
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from main import app
    from models.post import Post, PostMedia, PostDocument, Event, Like, Comment
    from models.user import User
    from models.university import University
    from routes import post

client = TestClient(app)

# Test data setup
def generate_mock_filename(user_id: int, ext: str) -> str:
    return f"{user_id}_mock{ext}"

fake_user = User(
    id=1,
    username="testuser",
    email="test@example.com",
    profile_picture="user.jpg"
)

fake_text_post = Post(
    id=1,
    user_id=1,
    content="This is a test post",
    post_type="text",
    created_at=datetime.now(ZoneInfo("UTC")),
    like_count=5,
    user=fake_user
)

fake_media_post = Post(
    id=2,
    user_id=1,
    content="Test media post",
    post_type="media",
    created_at=datetime.now(ZoneInfo("UTC")),
    like_count=0,
    user=fake_user
)

fake_document_post = Post(
    id=3,
    user_id=1,
    content="Test document post",
    post_type="document",
    created_at=datetime.now(ZoneInfo("UTC")),
    like_count=0,
    user=fake_user
)

fake_event_post = Post(
    id=4,
    user_id=1,
    content="Test event post",
    post_type="event",
    created_at=datetime.now(ZoneInfo("UTC")),
    like_count=0,
    user=fake_user
)

fake_media = PostMedia(
    id=1,
    post_id=1,  # Updated to match consistent ID
    media_url="1_mock.jpg",  # Use consistent mock filename
    media_type=".jpg"
)

fake_document = PostDocument(
    id=1,
    post_id=1,  # Updated to match consistent ID
    document_url="1_mock.pdf",  # Use consistent mock filename
    document_type=".pdf"
)

fake_event = Event(
    id=1,
    post_id=1,  # Updated to match consistent ID
    user_id=1,
    title="Test Event",
    description="Test event description",
    event_datetime=datetime.now(ZoneInfo("UTC")),
    location="Test Location",
    image_url=None
)

@pytest.fixture
def override_dependencies(monkeypatch):
    mock_session = MagicMock(spec=Session)

    # Mock database operations
    def mock_add(obj):
        if isinstance(obj, Post):
            obj.id = 1
            obj.user_id = fake_user.id
            obj.created_at = datetime.now(ZoneInfo("UTC"))
        elif isinstance(obj, PostMedia):
            obj.id = 1
            obj.post_id = 1
            obj.media_url = "1_mock.jpg"
            obj.media_type = ".jpg"
        elif isinstance(obj, PostDocument):
            obj.id = 1
            obj.post_id = 1
            obj.document_url = "1_mock.pdf"
            obj.document_type = ".pdf"
        elif isinstance(obj, Event):
            obj.id = 1
            obj.post_id = 1
            obj.user_id = fake_user.id
        return None

    mock_session.add.side_effect = mock_add
    mock_session.delete.return_value = None
    mock_session.commit.return_value = None
    mock_session.refresh.side_effect = lambda x: None

    # Mock queries
    def mock_post_filter(*args, **kwargs):
        mock = MagicMock()
        mock.first.return_value = fake_text_post
        mock.all.return_value = [fake_text_post]
        return mock

    mock_post_query = MagicMock()
    mock_post_query.filter.side_effect = mock_post_filter
    mock_post_query.filter_by.side_effect = mock_post_filter
    mock_post_query.order_by.return_value = mock_post_query
    mock_post_query.offset.return_value = mock_post_query
    mock_post_query.limit.return_value = mock_post_query
    mock_post_query.all.return_value = [fake_text_post]

    # Mock media, document and event queries
    mock_media_query = MagicMock()
    mock_media_query.filter.return_value.first.return_value = fake_media

    mock_document_query = MagicMock()
    mock_document_query.filter.return_value.first.return_value = fake_document

    mock_event_query = MagicMock()
    mock_event_query.filter.return_value.first.return_value = fake_event
    mock_event_query.all.return_value = [fake_event]

    # Configure query side effects
    def get_query_mock(model):
        if isinstance(model, type) and model == Post:
            return mock_post_query
        elif isinstance(model, type) and model == PostMedia:
            return mock_media_query
        elif isinstance(model, type) and model == PostDocument:
            return mock_document_query
        elif isinstance(model, type) and model == Event:
            return mock_event_query
        elif isinstance(model, type) and model == University:
            return MagicMock()
        return MagicMock()

    mock_session.query.side_effect = get_query_mock

    # Mock moderate_text
    mock_moderate_text = MagicMock()
    mock_moderate_text.return_value = False
    monkeypatch.setattr(post, "moderate_text", mock_moderate_text)

    def _get_db_override():
        return mock_session

    def _get_current_user_override():
        return fake_user

    app.dependency_overrides[post.get_db] = _get_db_override
    app.dependency_overrides[post.get_current_user] = _get_current_user_override

    yield mock_session, mock_moderate_text

    app.dependency_overrides.clear()

# def test_create_text_post(override_dependencies):
#     session, _ = override_dependencies

#     # Test data
#     test_content = "Test post content"

#     # Send request to create text post
#     response = client.post(
#         "/posts/create_text_post/",
#         data={"content": test_content}
#     )

#     assert response.status_code == 200
#     data = response.json()
#     assert data["id"] == 1
#     assert data["user_id"] == fake_user.id
#     assert data["content"] == test_content
#     assert data["post_type"] == "text"
#     assert "created_at" in data
#     assert data["comment_count"] == 0
#     assert data["user_liked"] is False

#     # Ensure database operations are called
#     session.add.assert_called()
#     session.commit.assert_called()
#     session.refresh.assert_called()

def test_create_text_post_with_inappropriate_content(override_dependencies):
    session, mock_moderate_text = override_dependencies
    mock_moderate_text.return_value = True  # Simulate inappropriate content detection

    # Send request with inappropriate content
    response = client.post(
        "/posts/create_text_post/",
        data={"content": "Inappropriate content"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Inappropriate content detected"
    session.add.assert_not_called()
    session.commit.assert_not_called()

# def test_get_posts(override_dependencies):
#     session, _ = override_dependencies

#     # Send request to get posts
#     response = client.get("/posts/")

#     assert response.status_code == 200
#     data = response.json()
#     assert "posts" in data
#     assert len(data["posts"]) == 1
#     assert "count" in data
#     assert data["count"] == 1

#     post = data["posts"][0]
#     assert post["id"] == fake_text_post.id
#     assert post["user_id"] == fake_text_post.user_id
#     assert post["content"] == fake_text_post.content
#     assert post["post_type"] == fake_text_post.post_type
#     assert "created_at" in post
#     assert post["total_likes"] == fake_text_post.like_count
#     assert "user" in post
#     assert post["user"]["id"] == fake_user.id
#     assert post["user"]["username"] == fake_user.username
#     assert post["user"]["profile_picture"] == f"http://127.0.0.1:8000/uploads/profile_pictures/{fake_user.profile_picture}"

# def test_get_single_post(override_dependencies):
#     session, _ = override_dependencies

#     # Send request to get a single post
#     response = client.get("/posts/1")

#     assert response.status_code == 200
#     data = response.json()
#     assert data["id"] == fake_text_post.id
#     assert data["user_id"] == fake_text_post.user_id
#     assert data["content"] == fake_text_post.content
#     assert data["post_type"] == fake_text_post.post_type
#     assert "created_at" in data
#     assert data["total_likes"] == fake_text_post.like_count
#     assert "user" in data
#     assert data["user"]["id"] == fake_user.id
#     assert data["user"]["username"] == fake_user.username
#     assert data["user"]["profile_picture"] == f"http://127.0.0.1:8000/uploads/profile_pictures/{fake_user.profile_picture}"

def test_get_single_post_not_found(override_dependencies):
    session, _ = override_dependencies
    
    # Mock post query to return None
    mock_post_query = MagicMock()
    mock_post_query.filter.return_value.first.return_value = None
    session.query.side_effect = lambda model: mock_post_query if model == Post else MagicMock()

    # Send request to get a non-existent post
    response = client.get("/posts/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Post not found"

# Media post tests
# def test_create_media_post(override_dependencies):
#     session, _ = override_dependencies

#     # Create test file content
#     test_content = "Test media post content"
#     test_file = {
#         "content": (None, test_content),
#         "media_file": ("test.jpg", b"test image content", "image/jpeg")
#     }

#     # Send request to create media post
#     response = client.post(
#         "/posts/create_media_post/",
#         files=test_file
#     )

#     assert response.status_code == 200
#     data = response.json()
#     assert data["id"] == 1
#     assert data["post_id"] == 1
#     assert data["media_url"] == fake_media.media_url
#     assert data["media_type"] == fake_media.media_type

#     # Ensure database operations are called
#     session.add.assert_called()
#     session.commit.assert_called()
#     session.refresh.assert_called()

# def test_create_media_post_invalid_type(override_dependencies):
#     session, _ = override_dependencies

#     # Create test file with invalid type
#     test_file = {
#         "content": (None, "Test content"),
#         "media_file": ("test.xyz", b"invalid content", "application/octet-stream")
#     }

#     # Send request with invalid file type
#     response = client.post(
#         "/posts/create_media_post/",
#         files=test_file
#     )

#     assert response.status_code == 400
#     assert "Invalid file type" in response.json()["detail"]
#     session.add.assert_not_called()
#     session.commit.assert_not_called()

# def test_update_media_post(override_dependencies):
#     session, _ = override_dependencies

#     # Test data
#     updated_content = "Updated media post content"
#     test_file = {
#         "content": (None, updated_content),
#         "media_file": ("updated.jpg", b"updated image content", "image/jpeg")
#     }

#     # Send request to update media post
#     response = client.put(
#         "/posts/update_media_post/1",
#         files=test_file
#     )

#     assert response.status_code == 200
#     data = response.json()
#     assert "message" in data
#     assert data["message"] == "Media post updated successfully"
#     assert "updated_post" in data
#     updated_post = data["updated_post"]
#     assert updated_post["id"] == fake_media_post.id
#     assert updated_post["user_id"] == fake_media_post.user_id
#     assert updated_post["content"] == updated_content
#     assert updated_post["post_type"] == "media"
#     assert "created_at" in updated_post
#     assert "media_url" in updated_post

# Document post tests
# def test_create_document_post(override_dependencies):
#     session, _ = override_dependencies

#     # Create test file content
#     test_content = "Test document post content"
#     test_file = {
#         "content": (None, test_content),
#         "document_file": ("test.pdf", b"test document content", "application/pdf")
#     }

#     # Send request to create document post
#     response = client.post(
#         "/posts/create_document_post/",
#         files=test_file
#     )

#     assert response.status_code == 200
#     data = response.json()
#     assert data["id"] == 1
#     assert data["post_id"] == 1
#     assert data["document_url"] == fake_document.document_url
#     assert data["document_type"] == fake_document.document_type

#     # Ensure database operations are called
#     session.add.assert_called()
#     session.commit.assert_called()
#     session.refresh.assert_called()

def test_create_document_post_invalid_type(override_dependencies):
    session, _ = override_dependencies

    # Create test file with invalid type
    test_file = {
        "content": (None, "Test content"),
        "document_file": ("test.xyz", b"invalid content", "application/octet-stream")
    }

    # Send request with invalid file type
    response = client.post(
        "/posts/create_document_post/",
        files=test_file
    )

    assert response.status_code == 400
    assert "Invalid file format" in response.json()["detail"]
    session.add.assert_not_called()
    session.commit.assert_not_called()

# def test_update_document_post(override_dependencies):
#     session, _ = override_dependencies

#     # Test data
#     updated_content = "Updated document post content"
#     test_file = {
#         "content": (None, updated_content),
#         "document_file": ("updated.pdf", b"updated document content", "application/pdf")
#     }

#     # Send request to update document post
#     response = client.put(
#         "/posts/update_document_post/1",
#         files=test_file
#     )

#     assert response.status_code == 200
#     data = response.json()
#     assert "message" in data
#     assert data["message"] == "Document post updated successfully"
#     assert "updated_post" in data
#     updated_post = data["updated_post"]
#     assert updated_post["id"] == fake_document_post.id
#     assert updated_post["user_id"] == fake_document_post.user_id
#     assert updated_post["content"] == updated_content
#     assert updated_post["post_type"] == "document"
#     assert "created_at" in updated_post
#     assert "document_url" in updated_post

# Event post tests
def test_create_event_post(override_dependencies):
    session, _ = override_dependencies

    # Test data
    test_data = {
        "content": "Test event post content",
        "event_title": "Test Event",
        "event_description": "Test event description",
        "event_date": "2025-04-23",
        "event_time": "14:00",
        "user_timezone": "UTC",
        "location": "Test Location"
    }

    # Send request to create event post
    response = client.post(
        "/posts/create_event_post/",
        data=test_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["post_id"] == 1
    assert data["user_id"] == fake_user.id
    assert data["title"] == test_data["event_title"]
    assert data["description"] == test_data["event_description"]
    assert data["location"] == test_data["location"]
    assert "event_datetime" in data
    assert data["image_url"] is None

    # Ensure database operations are called
    session.add.assert_called()
    session.commit.assert_called()
    session.refresh.assert_called()

def test_update_event_post(override_dependencies):
    session, _ = override_dependencies

    # Test data
    update_data = {
        "content": "Updated event content",
        "event_title": "Updated Event",
        "event_description": "Updated description",
        "event_date": "2025-04-24",
        "event_time": "15:00",
        "user_timezone": "UTC",
        "location": "Updated Location"
    }

    # Send request to update event post
    response = client.put(
        "/posts/update_event_post/1",
        data=update_data
    )

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    updated_post = data["updated_post"]
    assert updated_post["title"] == update_data["event_title"]
    assert updated_post["description"] == update_data["event_description"]
    assert updated_post["location"] == update_data["location"]
    assert "event_datetime" in updated_post

def test_delete_post(override_dependencies):
    session, _ = override_dependencies

    # Send request to delete post
    response = client.delete("/posts/delete_post/1")

    assert response.status_code == 200
    assert response.json()["message"] == "Post deleted successfully"
    session.delete.assert_called()
    session.commit.assert_called()

# def test_delete_post_not_found(override_dependencies):
#     session, _ = override_dependencies

#     # Mock post query to return None
#     mock_post_query = MagicMock()
#     mock_post_query.filter.return_value.first.return_value = None
#     session.query.side_effect = lambda model: mock_post_query if model == Post else MagicMock()

#     # Send request to delete non-existent post
#     response = client.delete("/posts/delete_post/999")

#     assert response.status_code == 404
#     assert response.json()["detail"] == "Post not found"

def test_get_events(override_dependencies):
    session, _ = override_dependencies

    # Send request to get all events
    response = client.get("/posts/events/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    event = data[0]
    assert event["id"] == fake_event.id
    assert event["post_id"] == fake_event.post_id
    assert event["user_id"] == fake_event.user_id
    assert event["title"] == fake_event.title
    assert event["description"] == fake_event.description
    assert event["location"] == fake_event.location
    assert "event_datetime" in event

def test_get_single_event(override_dependencies):
    session, _ = override_dependencies

    # Send request to get a specific event
    response = client.get("/posts/events/?event_id=1")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == fake_event.id
    assert data["post_id"] == fake_event.post_id
    assert data["user_id"] == fake_event.user_id
    assert data["title"] == fake_event.title
    assert data["description"] == fake_event.description
    assert data["location"] == fake_event.location
    assert "event_datetime" in data

def test_get_event_not_found(override_dependencies):
    session, _ = override_dependencies

    # Mock event query to return None
    mock_event_query = MagicMock()
    mock_event_query.filter.return_value.first.return_value = None
    session.query.side_effect = lambda model: mock_event_query if model == Event else MagicMock()

    # Send request to get non-existent event
    response = client.get("/posts/events/?event_id=999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"