import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
from zoneinfo import ZoneInfo
from fastapi import HTTPException

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
    # Create all mocks
    mock_session = MagicMock(spec=Session)
    mock_moderate_text = MagicMock()
    mock_get_post_by_id = MagicMock()
    mock_validate_file_extension = MagicMock()
    mock_generate_secure_filename = MagicMock()

    # Set common mock returns
    mock_moderate_text.return_value = False
    mock_get_post_by_id.return_value = fake_text_post
    mock_validate_file_extension.return_value = ".jpg"  # Default for media files
    mock_generate_secure_filename.return_value = "1_mock.jpg"  # Default for media files

    # Mock database operations
    def mock_add(obj):
        if isinstance(obj, Post):
            obj.id = 1
            obj.user_id = fake_user.id
            obj.created_at = datetime.now(ZoneInfo("UTC"))
            obj.hashtags = []
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
        elif isinstance(model, type) and model == Like:
            mock_like_query = MagicMock()
            mock_like_query.filter.return_value.first.return_value = None
            return mock_like_query
        return MagicMock()

    mock_session.query.side_effect = get_query_mock

    # Mock extract_hashtags
    mock_extract_hashtags = MagicMock()
    mock_extract_hashtags.return_value = []
    monkeypatch.setattr(post, "extract_hashtags", mock_extract_hashtags)

    monkeypatch.setattr(post, "moderate_text", mock_moderate_text)

    # Mock send_post_notifications
    mock_send_notifications = MagicMock()
    monkeypatch.setattr(post, "send_post_notifications", mock_send_notifications)

    # Mock helper functions
    mock_get_user_like_status = MagicMock()
    mock_get_user_like_status.return_value = False
    monkeypatch.setattr(post, "get_user_like_status", mock_get_user_like_status)

    mock_get_newer_posts = MagicMock()
    mock_get_newer_posts.return_value = mock_post_query
    monkeypatch.setattr(post, "get_newer_posts", mock_get_newer_posts)

    mock_get_post_additional_data = MagicMock()
    mock_get_post_additional_data.return_value = {}
    monkeypatch.setattr(post, "get_post_additional_data", mock_get_post_additional_data)

    # Set other mocks
    monkeypatch.setattr(post, "get_post_by_id", mock_get_post_by_id)
    monkeypatch.setattr(post, "validate_file_extension", mock_validate_file_extension)
    monkeypatch.setattr(post, "generate_secure_filename", mock_generate_secure_filename)
    
    mock_save_upload_file = MagicMock()
    monkeypatch.setattr(post, "save_upload_file", mock_save_upload_file)

    # Mock create_post_entry
    mock_create_post_entry = MagicMock()
    mock_create_post_entry.return_value = fake_text_post
    monkeypatch.setattr(post, "create_post_entry", mock_create_post_entry)

    # Mock post event helpers
    mock_get_post_and_event = MagicMock()
    mock_get_post_and_event.return_value = (fake_text_post, fake_event)
    monkeypatch.setattr(post, "get_post_and_event", mock_get_post_and_event)
    
    mock_update_post_and_event = MagicMock()
    mock_update_post_and_event.return_value = True
    monkeypatch.setattr(post, "update_post_and_event", mock_update_post_and_event)
    
    mock_format_updated_event_response = MagicMock()
    mock_format_updated_event_response.return_value = {
        "message": "Event post updated successfully",
        "updated_post": {
            "id": fake_text_post.id,
            "user_id": fake_text_post.user_id,
            "content": "Updated event content",
            "post_type": "event",
            "title": "Updated Event",
            "description": "Updated description",
            "event_datetime": datetime.now(ZoneInfo("UTC")).isoformat(),
            "location": "Updated Location"
        }
    }
    monkeypatch.setattr(post, "format_updated_event_response", mock_format_updated_event_response)
    
    mock_try_convert_datetime = MagicMock()
    mock_try_convert_datetime.return_value = datetime.now(ZoneInfo("UTC"))
    monkeypatch.setattr(post, "try_convert_datetime", mock_try_convert_datetime)

    def _get_db_override():
        return mock_session

    def _get_current_user_override():
        return fake_user

    app.dependency_overrides[post.get_db] = _get_db_override
    app.dependency_overrides[post.get_current_user] = _get_current_user_override

    # Create mocks dictionary 
    mocks = {
        "session": mock_session, 
        "moderate_text": mock_moderate_text,
        "get_post_by_id": mock_get_post_by_id,
        "validate_file_extension": mock_validate_file_extension,
        "generate_secure_filename": mock_generate_secure_filename
    }

    yield mocks

    app.dependency_overrides.clear()

# Text post tests 
# def test_create_text_post(override_dependencies):
#     mocks = override_dependencies
#     session = mocks["session"]

#     # Add hashtags attribute to fake_text_post
#     fake_text_post.hashtags = []

#     # Test data using Form data format
#     response = client.post(
#         "/posts/create_text_post/",
#         data={"content": "This is a test post"},
#         headers={"Content-Type": "application/x-www-form-urlencoded"}
#     )

#     assert response.status_code == 200
#     data = response.json()
#     assert data["id"] == 1
#     assert data["user_id"] == fake_user.id
#     assert data["content"] == "This is a test post"
#     assert data["post_type"] == "text"
#     assert "created_at" in data


# def test_create_text_post_with_inappropriate_content(override_dependencies):
#     mocks = override_dependencies
#     session = mocks["session"]
#     mock_moderate_text = mocks["moderate_text"]
#     mock_moderate_text.return_value = True  # Simulate inappropriate content detection

#     # Send request with Form data format
#     response = client.post(
#         "/posts/create_text_post/",
#         data={"content": "Inappropriate content"},
#         headers={"Content-Type": "application/x-www-form-urlencoded"}
#     )

#     assert response.status_code == 400
#     assert response.json()["detail"] == "Inappropriate content detected, Please revise your post."
#     session.add.assert_not_called()
#     session.commit.assert_not_called()

def test_get_posts(override_dependencies):
    mocks = override_dependencies
    session = mocks["session"]

    # Send request to get posts
    response = client.get("/posts/")

    assert response.status_code == 200
    data = response.json()
    assert "posts" in data
    assert len(data["posts"]) == 1
    assert "count" in data
    assert data["count"] == 1

    post = data["posts"][0]
    assert post["id"] == fake_text_post.id
    assert post["content"] == fake_text_post.content
    assert post["post_type"] == fake_text_post.post_type
    assert "created_at" in post
    assert post["total_likes"] == fake_text_post.like_count
    assert "user" in post
    assert post["user"]["id"] == fake_user.id
    assert post["user"]["username"] == fake_user.username

def test_get_single_post(override_dependencies):
    mocks = override_dependencies
    session = mocks["session"]

    # Send request to get a single post
    response = client.get("/posts/1")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == fake_text_post.id
    assert data["content"] == fake_text_post.content
    assert data["post_type"] == fake_text_post.post_type
    assert "created_at" in data
    assert data["total_likes"] == fake_text_post.like_count
    assert "user" in data
    assert data["user"]["id"] == fake_user.id
    assert data["user"]["username"] == fake_user.username

def test_get_single_post_not_found(override_dependencies):
    mocks = override_dependencies
    session = mocks["session"]
    
    # Mock post query to return None
    mock_post_query = MagicMock()
    mock_post_query.filter.return_value.first.return_value = None
    session.query.side_effect = lambda model: mock_post_query if model == Post else MagicMock()

    # Send request to get a non-existent post
    response = client.get("/posts/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Post not found"

# Media post tests
def test_create_media_post(override_dependencies):
    mocks = override_dependencies
    session = mocks["session"]
    mock_validate_file_extension = mocks["validate_file_extension"]
    mock_generate_secure_filename = mocks["generate_secure_filename"]
    
    # Set return values for media files
    mock_validate_file_extension.return_value = ".jpg"
    mock_generate_secure_filename.return_value = "1_mock.jpg"

    # Create test file content
    test_content = "Test media post content"
    test_file = {
        "content": (None, test_content),
        "media_file": ("test.jpg", b"test image content", "image/jpeg")
    }

    # Send request to create media post
    response = client.post(
        "/posts/create_media_post/",
        files=test_file
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["post_id"] == 1
    assert data["media_url"] == fake_media.media_url
    assert data["media_type"] == fake_media.media_type

    # Ensure database operations are called
    session.add.assert_called()
    session.commit.assert_called()
    session.refresh.assert_called()

def test_create_media_post_invalid_type(override_dependencies):
    mocks = override_dependencies
    session = mocks["session"] 
    mock_validate_file_extension = mocks["validate_file_extension"]

    # Mock validate_file_extension to raise HTTPException
    mock_validate_file_extension.side_effect = HTTPException(status_code=400, detail="Invalid file type")

    # Create test file with invalid type
    test_file = {
        "content": (None, "Test content"),
        "media_file": ("test.xyz", b"invalid content", "application/octet-stream")
    }

    # Send request with invalid file type
    response = client.post(
        "/posts/create_media_post/",
        files=test_file
    )

    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]
    # Check add was not called with a Post instance (it might be called with other objects)
    for call_args in session.add.call_args_list:
        if len(call_args[0]) > 0 and isinstance(call_args[0][0], Post):
            pytest.fail("session.add was called with a Post instance when it shouldn't have been")

def test_update_media_post(override_dependencies):
    mocks = override_dependencies
    session = mocks["session"]
    mock_validate_file_extension = mocks["validate_file_extension"]
    mock_generate_secure_filename = mocks["generate_secure_filename"]
    
    # Set return values for media files
    mock_validate_file_extension.return_value = ".jpg"
    mock_generate_secure_filename.return_value = "1_mock.jpg"

    # Test data
    updated_content = "Updated media post content"
    test_file = {
        "content": (None, updated_content),
        "media_file": ("updated.jpg", b"updated image content", "image/jpeg")
    }

    # Send request to update media post
    response = client.put(
        "/posts/update_media_post/1",
        files=test_file
    )

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Media post updated successfully"
    assert "updated_post" in data
    updated_post = data["updated_post"]
    assert updated_post["id"] == fake_text_post.id  # We use fake_text_post for consistency
    assert updated_post["content"] == updated_content
    assert updated_post["post_type"] == "text"
    assert "created_at" in updated_post
    assert "media_url" in updated_post

# Document post tests
# def test_create_document_post(override_dependencies):
#     mocks = override_dependencies
#     session = mocks["session"]
#     mock_validate_file_extension = mocks["validate_file_extension"]
#     mock_generate_secure_filename = mocks["generate_secure_filename"]
    
#     # Mock supabase upload
#     with patch("routes.post.upload_file_to_supabase") as mock_upload:
#         mock_upload.return_value = "mocked_document_url"
        
#         # Set return values for document files
#         mock_validate_file_extension.return_value = ".pdf"
#         mock_generate_secure_filename.return_value = "1_mock.pdf"

#         # Create test file content
#         test_content = "Test document post content"
#         test_file = {
#             "content": (None, test_content),
#             "document_file": ("test.pdf", b"test document content", "application/pdf")
#         }

#         # Send request to create document post
#         response = client.post(
#             "/posts/create_document_post/",
#             files=test_file
#         )

#         assert response.status_code == 200
#         data = response.json()
#         assert data["id"] == 1
#         assert data["post_id"] == 1
#         assert data["document_url"] == "mocked_document_url"  # Updated to match Supabase URL
#         assert data["document_type"] == ".pdf"

def test_create_document_post_invalid_type(override_dependencies):
    mocks = override_dependencies
    session = mocks["session"]
    mock_validate_file_extension = mocks["validate_file_extension"]

    # Mock validate_file_extension to raise HTTPException
    mock_validate_file_extension.side_effect = HTTPException(status_code=400, detail="Invalid file format")

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

def test_update_document_post(override_dependencies):
    mocks = override_dependencies
    session = mocks["session"]
    mock_validate_file_extension = mocks["validate_file_extension"]
    mock_generate_secure_filename = mocks["generate_secure_filename"]
    
    # Mock supabase upload
    with patch("routes.post.upload_file_to_supabase") as mock_upload:
        mock_upload.return_value = "mocked_document_url"
        
        # Set return values for document files
        mock_validate_file_extension.return_value = ".pdf"
        mock_generate_secure_filename.return_value = "1_mock.pdf"

        # Test data
        updated_content = "Updated document post content"
        test_file = {
            "content": (None, updated_content),
            "document_file": ("updated.pdf", b"updated document content", "application/pdf")
        }

        # Send request to update document post
        response = client.put(
            "/posts/update_document_post/1",
            files=test_file
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Document post updated successfully"
        assert "updated_post" in data
        updated_post = data["updated_post"]
        assert updated_post["id"] == fake_text_post.id
        assert updated_post["content"] == updated_content
        assert "document_url" in updated_post
        assert updated_post["document_url"] == "mocked_document_url"

# Event post tests
# def test_create_event_post(override_dependencies):
#     mocks = override_dependencies
#     session = mocks["session"]

#     # Test data with proper form format
#     test_data = {
#         "content": "Test event post content",
#         "event_title": "Test Event",
#         "event_description": "Test event description",
#         "event_date": "2025-04-23",
#         "event_time": "14:00",
#         "user_timezone": "UTC",
#         "location": "Test Location"
#     }

#     # Send request to create event post
#     response = client.post(
#         "/posts/create_event_post/",
#         data=test_data,
#         headers={"Content-Type": "application/x-www-form-urlencoded"}
#     )

#     assert response.status_code == 200
#     data = response.json()
#     assert data["id"] == 1
#     assert data["post_id"] == 1
#     assert data["user_id"] == fake_user.id
#     assert data["title"] == test_data["event_title"]
#     assert data["description"] == test_data["event_description"]
#     assert data["location"] == test_data["location"]
#     assert "event_datetime" in data
#     assert data["image_url"] is None

# def test_update_event_post(override_dependencies):
#     mocks = override_dependencies
#     session = mocks["session"]

#     # Test data
#     update_data = {
#         "content": "Updated event content",
#         "event_title": "Updated Event",
#         "event_description": "Updated description",
#         "event_date": "2025-04-24",
#         "event_time": "15:00",
#         "user_timezone": "UTC",
#         "location": "Updated Location"
#     }

#     # Send request to update event post
#     response = client.put(
#         "/posts/update_event_post/1",
#         data=update_data
#     )

#     assert response.status_code == 200
#     data = response.json()
#     assert "message" in data
#     assert data["message"] == "Event post updated successfully"
#     assert "updated_post" in data
#     updated_post = data["updated_post"]
#     assert updated_post["title"] == update_data["event_title"]
#     assert updated_post["description"] == update_data["event_description"]
#     assert updated_post["location"] == update_data["location"]
#     assert "event_datetime" in updated_post

def test_delete_post(override_dependencies):
    mocks = override_dependencies
    session = mocks["session"]

    # Send request to delete post
    response = client.delete("/posts/delete_post/1")

    assert response.status_code == 200
    assert response.json()["message"] == "Post deleted successfully"
    session.delete.assert_called()
    session.commit.assert_called()

def test_delete_post_not_found(override_dependencies):
    mocks = override_dependencies
    session = mocks["session"]
    mock_get_post_by_id = mocks["get_post_by_id"]

    # Mock get_post_by_id to raise HTTPException
    mock_get_post_by_id.side_effect = HTTPException(status_code=404, detail="Post not found")

    # Send request to delete non-existent post
    response = client.delete("/posts/delete_post/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Post not found"

# def test_get_events(override_dependencies):
#     mocks = override_dependencies
#     session = mocks["session"]

#     # Send request to get all events
#     response = client.get("/posts/events/")

#     assert response.status_code == 200
#     data = response.json()
#     assert isinstance(data, list)
#     assert len(data) >= 1
#     event = data[0]
#     assert event["id"] == fake_event.id
#     assert event["post_id"] == fake_event.post_id
#     assert event["user_id"] == fake_event.user_id
#     assert event["title"] == fake_event.title
#     assert event["description"] == fake_event.description
#     assert event["location"] == fake_event.location
#     assert "event_datetime" in event

# def test_get_single_event(override_dependencies):
#     mocks = override_dependencies
#     session = mocks["session"]

#     # Send request to get a specific event
#     response = client.get("/posts/events/1")

#     assert response.status_code == 200
#     data = response.json()
#     assert data["id"] == fake_event.id
#     assert data["post_id"] == fake_event.post_id
#     assert data["title"] == fake_event.title
#     assert data["description"] == fake_event.description
#     assert data["location"] == fake_event.location
#     assert "event_datetime" in data

def test_get_event_not_found(override_dependencies):
    mocks = override_dependencies
    session = mocks["session"]

    # Mock event query to return None
    mock_event_query = MagicMock()
    mock_event_query.filter.return_value.first.return_value = None
    session.query.side_effect = lambda model: mock_event_query if model == Event else MagicMock()

    # Send request to get non-existent event
    response = client.get("/posts/events/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Not Found"