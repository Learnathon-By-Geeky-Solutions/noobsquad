import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, patch
import os
import shutil
import io
from PIL import Image

# Add backend directory to sys.path for imports
sys.path.append(str(Path(__file__).resolve().parents[1]))

from main import app
from models.user import User
from schemas.user import UserResponse
from models.university import University
from core.security import hash_password
from core.dependencies import get_db
from database.session import SessionLocal

# Create test client
client = TestClient(app)

# Test user data
test_user = User(
    id=1,
    username="testuser",
    email="test@example.com",
    hashed_password=hash_password("testpass"),
    is_active=True,
    is_verified=True,
    profile_picture=None,
    university_name=None,
    department=None,
    fields_of_interest=None,
    profile_completed=False
)

# Fixture to override dependencies
@pytest.fixture(autouse=True)
def override_dependencies(monkeypatch):
    mock_session = MagicMock(spec=Session)
    
    def _get_db_override():
        return mock_session
    
    def _get_current_user_override():
        return test_user
    
    # Override dependencies
    app.dependency_overrides[get_db] = _get_db_override
    
    # Find the actual get_current_user used in profile.py
    from api.v1.endpoints.auth import get_current_user
    app.dependency_overrides[get_current_user] = _get_current_user_override
    
    yield mock_session
    
    app.dependency_overrides.clear()

# Mock the file upload directory
@pytest.fixture
def mock_upload_dir():
    original_dir = os.path.join(os.getcwd(), "uploads", "profile_pictures")
    test_dir = os.path.join(os.getcwd(), "test_uploads", "profile_pictures")
    
    # Create test directory
    os.makedirs(test_dir, exist_ok=True)
    
    # Mock the UPLOAD_DIR in the module
    with patch("routes.profile.UPLOAD_DIR", test_dir):
        yield test_dir
    
    # Clean up test directory after tests
    if os.path.exists(test_dir):
        shutil.rmtree(os.path.dirname(test_dir))

# Create a test image
@pytest.fixture
def test_image():
    image = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr

# Test complete_profile_step1 endpoint - success case
def test_complete_profile_step1_success(override_dependencies):
    mock_session = override_dependencies
    
    # Mock user query
    mock_user_query = MagicMock()
    mock_user_query.filter.return_value.first.return_value = test_user
    
    # Mock university query
    mock_uni_query = MagicMock()
    mock_uni = University(
        id=1,
        name="Test University",
        departments=["Computer Science"],
        total_members=1
    )
    mock_uni_query.filter.return_value.first.return_value = mock_uni
    
    # Mock count query
    mock_count_query = MagicMock()
    mock_count_query.filter.return_value.count.return_value = 1
    
    # Configure session to return appropriate queries
    def get_query(model):
        if model == User:
            return mock_user_query
        elif model == University:
            return mock_uni_query
        return mock_count_query
    
    mock_session.query = get_query
    
    # Make the request
    response = client.post(
        "/profile/step1",
        data={
            "university_name": "Test University",
            "department": "Computer Science",
            "fields_of_interest": ["Artificial Intelligence", "Data Science"]
        }
    )
    
    # Assertions
    assert response.status_code == 200
    
    # Verify user was updated correctly
    assert test_user.university_name == "Test University"
    assert test_user.department == "Computer Science"
    assert test_user.fields_of_interest == "Artificial Intelligence,Data Science"
    assert test_user.profile_completed is True
    
    # Verify db operations
    mock_session.commit.assert_called()
    mock_session.refresh.assert_called_with(test_user)

# Test complete_profile_step1 endpoint - user not found
def test_complete_profile_step1_user_not_found(override_dependencies):
    mock_session = override_dependencies
    
    # Mock user query to return None (user not found)
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = None
    mock_session.query.return_value = mock_query
    
    # Make the request
    response = client.post(
        "/profile/step1",
        data={
            "university_name": "Test University",
            "department": "Computer Science",
            "fields_of_interest": ["Artificial Intelligence", "Data Science"]
        }
    )
    
    # Assertions
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

# Test complete_profile_step1 endpoint - create new university
def test_complete_profile_step1_new_university(override_dependencies):
    mock_session = override_dependencies
    
    # Mock user query
    mock_user_query = MagicMock()
    mock_user_query.filter.return_value.first.return_value = test_user
    
    # Mock university query - university not found then found after creation
    mock_uni_query = MagicMock()
    # First call - not found
    mock_uni_query.filter.return_value.first.side_effect = [None, MagicMock()]
    
    # Mock count query
    mock_count_query = MagicMock()
    mock_count_query.filter.return_value.count.return_value = 1
    
    # Configure session to return appropriate queries
    def get_query(model):
        if model == User:
            return mock_user_query
        elif model == University:
            return mock_uni_query
        return mock_count_query
    
    mock_session.query = get_query
    
    # Make the request
    response = client.post(
        "/profile/step1",
        data={
            "university_name": "New University",
            "department": "Physics",
            "fields_of_interest": ["Physics", "Mathematics"]
        }
    )
    
    # Assertions
    assert response.status_code == 200
    
    # Verify University was created
    mock_session.add.assert_called()
    mock_session.commit.assert_called()
    
    # Verify user was updated
    assert test_user.university_name == "New University"
    assert test_user.department == "Physics"
    assert test_user.fields_of_interest == "Physics,Mathematics"
    assert test_user.profile_completed is True

# Test upload_profile_picture endpoint - success case
def test_upload_profile_picture_success(override_dependencies, mock_upload_dir, test_image):
    mock_session = override_dependencies
    
    # Mock user query
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = test_user
    mock_session.query.return_value = mock_query
    
    # Mock the secrets.token_hex function to return a predictable value
    with patch("secrets.token_hex", return_value="mocktoken"):
        # Make the request
        response = client.post(
            "/profile/upload_picture",
            files={"file": ("test_image.jpg", test_image, "image/jpeg")}
        )
    
    # Assertions
    assert response.status_code == 200
    result = response.json()
    assert "filename" in result
    assert result["filename"] == "1_mocktoken.jpg"
    assert "profile_url" in result
    assert result["profile_completed"] == test_user.profile_completed
    
    # Verify user was updated
    assert test_user.profile_picture == "1_mocktoken.jpg"
    mock_session.commit.assert_called()
    mock_session.refresh.assert_called_with(test_user)
    
    # Verify file was saved (if using real file operations)
    if os.path.exists(mock_upload_dir):
        file_path = os.path.join(mock_upload_dir, "1_mocktoken.jpg")
        assert os.path.exists(file_path)

# Test upload_profile_picture endpoint - user not found
def test_upload_profile_picture_user_not_found(override_dependencies, test_image):
    mock_session = override_dependencies
    
    # Mock user query to return None (user not found)
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = None
    mock_session.query.return_value = mock_query
    
    # Make the request
    response = client.post(
        "/profile/upload_picture",
        files={"file": ("test_image.jpg", test_image, "image/jpeg")}
    )
    
    # Assertions
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

# Test upload_profile_picture endpoint - invalid file type
def test_upload_profile_picture_invalid_file_type(override_dependencies):
    mock_session = override_dependencies
    
    # Mock user query
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = test_user
    mock_session.query.return_value = mock_query
    
    # Create a text file
    text_file = io.BytesIO(b"This is not an image file")
    
    # Make the request
    response = client.post(
        "/profile/upload_picture",
        files={"file": ("test_file.txt", text_file, "text/plain")}
    )
    
    # Assertions
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid file type. Allowed: jpg, jpeg, png, gif, webp."}
