import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch
from main import app
from database.session import Base, SessionLocal, engine
from core.dependencies import get_db
from models.user import User
from models.post import Post, PostMedia, PostDocument, Event
from core.security import hash_password
import os
import shutil
from datetime import datetime
from zoneinfo import ZoneInfo

# Add backend directory to sys.path for imports
sys.path.append(str(Path(__file__).resolve().parents[1]))


# Ensure tables exist before testing
Base.metadata.create_all(bind=engine)

# Override dependency for testing
def override_get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Initialize FastAPI test client
client = TestClient(app)

# ----------------------
# 🔧 Fixture for setup and teardown
# ----------------------
@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Setup: Create tables and clear upload directories
    Base.metadata.create_all(bind=engine)
    for dir_path in ["uploads/media", "uploads/document", "uploads/event_images"]:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
        os.makedirs(dir_path, exist_ok=True)
    
    yield
    
    # Teardown: Drop tables and remove upload directories
    Base.metadata.drop_all(bind=engine)
    for dir_path in ["uploads/media", "uploads/document", "uploads/event_images"]:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)

# ----------------------
# 🔧 Fixture for test user
# ----------------------
@pytest.fixture
def test_user():
    db = SessionLocal()
    user = db.query(User).filter(User.email == "test@example.com").first()
    if not user:
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            hashed_password=hash_password("testpass"),
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    db.close()
    return user

# ----------------------
# 🔧 Fixture for auth headers
# ----------------------
@pytest.fixture
def auth_headers(test_user):
    response = client.post(
        "/auth/token",
        data={
            "username": "testuser",
            "password": "testpass"
        }
    )
    assert response.status_code == 200, "Failed to obtain token"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# ... (previous imports and setup remain unchanged)

# ----------------------
# ✅ Test get_posts
# ----------------------
@patch("services.services.get_newer_posts")
@patch("services.services.get_user_like_status")
@patch("services.services.get_post_additional_data")
def test_get_posts_success(mock_additional_data, mock_like_status, mock_newer_posts, auth_headers, test_user):
    # Mock service functions
    mock_post = Post(id=1, user_id=test_user.id, content="Test post", post_type="text", created_at=datetime.now(), like_count=0)
    mock_post.user = test_user
    mock_query = mock_newer_posts.return_value.order_by.return_value.offset.return_value.limit.return_value
    mock_query.all.return_value = [mock_post]
    
    mock_like_status.return_value = False
    mock_additional_data.return_value = {}

    # Fallback: Add post to database
    db = SessionLocal()
    db_post = Post(id=1, user_id=test_user.id, content="Test post", post_type="text", created_at=datetime.now(), like_count=0)
    db.add(db_post)
    db.commit()
    db.close()

    response = client.get(
        "/posts",
        params={"limit": 10, "offset": 0},
        headers=auth_headers
    )
    
    print(f"Response: {response.json()}")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
    data = response.json()
    assert data["count"] == 1, f"Expected count 1, got {data['count']}"
    assert data["posts"][0]["content"] == "Test post"
    assert data["posts"][0]["user"]["username"] == "testuser"

# ----------------------
# ✅ Test create_media_post
# ----------------------
@patch("services.services.create_post_entry")
@patch("services.services.send_post_notifications")
def test_create_media_post_success(mock_notifications, mock_create_post, auth_headers, test_user, tmp_path):
    mock_post = Post(id=1, user_id=test_user.id, content="Media post", post_type="media")
    mock_create_post.return_value = mock_post

    image_path = tmp_path / "test_image.jpg"
    with open(image_path, "wb") as f:
        f.write(b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00")

    with open(image_path, "rb") as f:
        response = client.post(
            "/posts/create_media_post/",  # Updated URL
            files={"media_file": ("test_image.jpg", f, "image/jpeg")},
            data={"content": "Media post"},
            headers=auth_headers
        )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
    data = response.json()
    assert data["post_id"] == 1
    assert data["media_type"] == ".jpg"
    assert os.path.exists(os.path.join("uploads/media", data["media_url"]))
    


 
# ----------------------
# ✅ Test get_single_post
# ----------------------
@patch("services.services.get_user_like_status")
@patch("services.services.get_post_additional_data")
def test_get_single_post_success(mock_additional_data, mock_like_status, auth_headers, test_user):
    db = SessionLocal()
    post = Post(id=1, user_id=test_user.id, content="Test post", post_type="text", created_at=datetime.now(), like_count=0)
    db.add(post)
    db.commit()
    db.close()

    mock_like_status.return_value = False
    mock_additional_data.return_value = {}

    response = client.get("/posts/1", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["content"] == "Test post"
# ----------------------
# ✅ Test create_document_post
# ----------------------
@patch("services.services.create_post_entry")
@patch("services.services.send_post_notifications")
def test_create_document_post_success(mock_notifications, mock_create_post, auth_headers, test_user, tmp_path):
    mock_post = Post(id=1, user_id=test_user.id, content="Doc post", post_type="document")
    mock_create_post.return_value = mock_post

    doc_path = tmp_path / "test_doc.pdf"
    with open(doc_path, "wb") as f:
        f.write(b"%PDF-1.4")

    with open(doc_path, "rb") as f:
        response = client.post(
            "/posts/create_document_post/",
            files={"document_file": ("test_doc.pdf", f, "application/pdf")},
            data={"content": "Doc post"},
            headers=auth_headers
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["post_id"] == 1
    assert data["document_type"] == ".pdf"
    assert os.path.exists(os.path.join("uploads/document", data["document_url"]))

# ----------------------
# ✅ Test create_text_post
# ----------------------

# @patch("services.services.create_post_entry")
# @patch("services.services.send_post_notifications")
# @patch("AI.moderation.moderate_text")
# def test_create_text_post_success(mock_moderate, mock_notifications, mock_create_post, auth_headers, test_user):
#     mock_post = Post(id=1, user_id=test_user.id, content="Text post", post_type="text")
#     mock_create_post.return_value = mock_post
#     mock_moderate.return_value = False

#     headers = auth_headers.copy()
#     headers["Content-Type"] = "application/x-www-form-urlencoded"

#     response = client.post(
#         "/posts/create_text_post/",
#         data={"content": "Text post"},
#         headers=headers
#     )

#     print("RESPONSE STATUS:", response.status_code)
#     print("RESPONSE TEXT:", response.text)

#     assert response.status_code == 200
#     data = response.json()
#     assert data["id"] == 1
#     assert data["content"] == "Text post"

# ----------------------
# ✅ Test create_event_post
# ----------------------
@patch("services.services.create_post_entry")
@patch("services.services.send_post_notifications")
def test_create_event_post_success(mock_notifications, mock_create_post, auth_headers, test_user, tmp_path):
    mock_post = Post(id=1, user_id=test_user.id, content="Event post", post_type="event")
    mock_create_post.return_value = mock_post

    image_path = tmp_path / "event_image.jpg"
    with open(image_path, "wb") as f:
        f.write(b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00")

    with open(image_path, "rb") as f:
        response = client.post(
            "/posts/create_event_post/",
            files={"event_image": ("event_image.jpg", f, "image/jpeg")},
            data={
                "content": "Event post",
                "event_title": "Test Event",
                "event_description": "Event description",
                "event_date": "2025-04-20",
                "event_time": "14:00",
                "user_timezone": "Asia/Dhaka",
                "location": "Dhaka"
            },
            headers=auth_headers
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["post_id"] == 1
    assert data["title"] == "Test Event"
    assert os.path.exists(Path(data["image_url"].replace("http://127.0.0.1:8000/", "")))

# ----------------------
# ✅ Test get_posts_by_user
# ----------------------
def test_get_posts_by_user_success(auth_headers, test_user):
    db = SessionLocal()
    post = Post(id=1, user_id=test_user.id, content="User post", post_type="text", created_at=datetime.now())
    db.add(post)
    db.commit()
    db.close()

    response = client.get("/posts/posts/", params={"user_id": test_user.id})
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "User post"

# ----------------------
# ✅ Test update_text_post
# ----------------------
# @patch("services.services.get_post_by_id")
# @patch("services.services.update_post_content")
# def test_update_text_post_success(mock_update_content, mock_get_post, auth_headers, test_user):
#     mock_post = Post(id=3, user_id=test_user.id, content="Old content", post_type="text")
#     mock_get_post.return_value = mock_post

#     response = client.put(
#         "/posts/update_text_post/3",
#         data={"content": "Text post"},
#         headers=auth_headers
#     )
    
#     assert response.status_code == 200
#     data = response.json()
#     assert data["content"] == "New content"

# ----------------------
# ✅ Test update_media_post
# ----------------------
# @patch("services.services.get_post_by_id")
# @patch("services.services.update_post_content")
# @patch("services.services.remove_old_file_if_exists")
# def test_update_media_post_success(mock_remove_file, mock_update_content, mock_get_post, auth_headers, test_user, tmp_path):
#     mock_post = Post(id=15, user_id=test_user.id, content="Old content", post_type="media")
#     mock_get_post.return_value = mock_post

#     image_path = tmp_path / "new_image.jpg"
#     with open(image_path, "wb") as f:
#         f.write(b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00")

#     with open(image_path, "rb") as f:
#         response = client.put(
#             "/posts/update_media_post/15",
#             files={"media_file": ("new_image.jpg", f, "image/jpeg")},
#             data={"content": "New content"},
#             headers=auth_headers
#         )
    
#     assert response.status_code == 200
#     data = response.json()
#     assert data["message"] == "Media post updated successfully"
#     assert data["updated_post"]["content"] == "New content"
#     assert os.path.exists(os.path.join("uploads/media", data["updated_post"]["media_url"]))

# ----------------------
# ✅ Test update_document_post
# ----------------------
# @patch("services.services.get_post_by_id")
# @patch("services.services.update_post_content")
# @patch("services.services.remove_old_file_if_exists")
# def test_update_document_post_success(mock_remove_file, mock_update_content, mock_get_post, auth_headers, test_user, tmp_path):
#     mock_post = Post(id=1, user_id=test_user.id, content="Old content", post_type="document")
#     mock_get_post.return_value = mock_post

#     doc_path = tmp_path / "new_doc.pdf"
#     with open(doc_path, "wb") as f:
#         f.write(b"%PDF-1.4")

#     with open(doc_path, "rb") as f:
#         response = client.put(
#             "/posts/update_document_post/1",
#             files={"document_file": ("new_doc.pdf", f, "application/pdf")},
#             data={"content": "New content"},
#             headers=auth_headers
#         )
    
#     assert response.status_code == 200
#     data = response.json()
#     assert data["message"] == "Document post updated successfully"
#     assert data["updated_post"]["content"] == "New content"
#     assert os.path.exists(os.path.join("uploads/document", data["updated_post"]["document_url"]))

# ----------------------
# ✅ Test update_event_post
# ----------------------
# @patch("services.services.get_post_and_event")
# @patch("services.services.update_post_and_event")
# @patch("services.services.format_updated_event_response")
# def test_update_event_post_success(mock_format_response, mock_update, mock_get, auth_headers, test_user):
#     mock_post = Post(id=1, user_id=test_user.id, content="Old content", post_type="event")
#     mock_event = Event(post_id=1, user_id=test_user.id, title="Old title")
#     mock_get.return_value = (mock_post, mock_event)
#     mock_update.return_value = True
#     mock_format_response.return_value = {"id": 1, "content": "New content", "title": "New title"}

#     response = client.put(
#         "/posts/update_event_post/1",
#         data={
#             "content": "New content",
#             "event_title": "New title",
#             "event_description": "New description",
#             "event_date": "2025-04-20",
#             "event_time": "4:00",
#             "user_timezone": "Asia/Dhaka",
#             "location": "Dhaka"
#         },
#         headers=auth_headers
#     )
    
#     assert response.status_code == 200
#     data = response.json()
#     assert data["content"] == "New content"
#     assert data["title"] == "New title"

# ----------------------
# ✅ Test delete_post
# ----------------------

# @patch("services.services.delete_post_by_id")  # Mocking the deletion function
# def test_delete_post_success(mock_delete_post, mock_get_post, auth_headers, test_user):
#     mock_post = Post(id=1, user_id=test_user.id, content="Test post", post_type="text", created_at=datetime.now(), like_count=0)
    
#     # Mock the return value of get_post_by_id
#     mock_get_post.return_value = mock_post
    
#     # Mock the deletion logic to return True (indicating successful deletion)
#     mock_delete_post.return_value = True

#     response = client.delete("/posts/delete_post/1", headers=auth_headers)
    
#     assert response.status_code == 200
#     assert response.json()["message"] == "Post deleted successfully"


def test_get_events_success(auth_headers, test_user):
    db = SessionLocal()

    # Create and insert a post record with post_id = 100
    post = Post(id=100, user_id=test_user.id, content="Test Post")
    db.add(post)
    db.commit()

    # Now create the event with post_id = 100 (which should now exist in the posts table)
    event = Event(
        id=100,
        post_id=100,  # Valid post_id
        user_id=test_user.id,
        title="Test Event",
        description="Event description",
        event_datetime=datetime.now(tz=ZoneInfo("UTC")),
        location="Dhaka"
    )
    db.add(event)
    db.commit()
    db.close()

    response = client.get("/posts/events/", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Event"

def test_get_single_event_success(auth_headers, test_user):
    db = SessionLocal()

    # Create and insert a post record with post_id = 25
    post = Post(id=25, user_id=test_user.id, content="Test Post")
    db.add(post)
    db.commit()

    # Now create the event with post_id = 25 (which should now exist in the posts table)
    event = Event(
        id=25,
        post_id=25,  # Valid post_id
        user_id=test_user.id,
        title="Test Event",
        description="Event description",
        event_datetime=datetime.now(tz=ZoneInfo("UTC")),
        location="Dhaka"
    )
    db.add(event)
    db.commit()
    db.close()

    response = client.get("/posts/events/", params={"event_id": 25}, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 25
    assert data["title"] == "Test Event"

# ----------------------
# ✅ Test unauthorized access
# ----------------------
def test_get_posts_unauthorized():
    response = client.get("/posts/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"