import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import MagicMock
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from main import app
from models.user import User
from models.post import Post
from schemas.university import UniversityPage, Member
from core.dependencies import get_db
from routes.group import get_university_info

# Create test client
client = TestClient(app)

# Fake data for testing
fake_user1 = User(
    id=1,
    username="user1",
    email="user1@example.com",
    university_name="TestUniversity",
    department="Computer Science"
)
fake_user2 = User(
    id=2,
    username="user2",
    email="user2@example.com",
    university_name="TestUniversity",
    department="Mathematics"
)
fake_post = Post(
    id=1,
    user_id=1,
    content="Great day at #testuniversity!",
    created_at="2023-10-01T12:00:00"
)

# Fixture to override dependencies
@pytest.fixture(autouse=True)
def override_dependencies():
    mock_session = MagicMock(spec=Session)

    def _get_db_override():
        return mock_session

    app.dependency_overrides[get_db] = _get_db_override

    yield mock_session

    app.dependency_overrides.clear()

# Test successful retrieval of university info
def test_get_university_info_success(override_dependencies):
    mock_session = override_dependencies

    # Mock user query
    mock_user_query = MagicMock()
    mock_user_query.filter.return_value.all.return_value = [fake_user1, fake_user2]

    # Mock post query
    mock_post_query = MagicMock()
    mock_post_query.filter.return_value.order_by.return_value.all.return_value = [fake_post]

    # Configure query to return appropriate mocks based on model
    def query_mock(model):
        if model == User:
            return mock_user_query
        elif model == Post:
            return mock_post_query
        return MagicMock()

    mock_session.query.side_effect = query_mock

    # Send GET request
    response = client.get("/universities/TestUniversity")
    assert response.status_code == 200
    data = response.json()

    # Verify response
    assert data["university"] == "TestUniversity"
    assert data["total_members"] == 2
    assert data["departments"] == {
        "Computer Science": [{"username": "user1", "email": "user1@example.com"}],
        "Mathematics": [{"username": "user2", "email": "user2@example.com"}]
    }
    assert data["post_ids"] == [1]

# Test when no users are found
def test_get_university_info_no_users(override_dependencies):
    mock_session = override_dependencies

    # Mock user query to return empty list
    mock_user_query = MagicMock()
    mock_user_query.filter.return_value.all.return_value = []
    mock_session.query.side_effect = lambda model: mock_user_query if model == User else MagicMock()

    # Send GET request
    response = client.get("/universities/NonExistentUniversity")
    assert response.status_code == 500
    assert response.json()["detail"] == "404: University not found"

# Test when an internal server error occurs
def test_get_university_info_internal_error(override_dependencies):
    mock_session = override_dependencies

    # Mock session to raise an exception
    mock_session.query.side_effect = Exception("Database error")

    # Send GET request
    response = client.get("/universities/TestUniversity")
    assert response.status_code == 500
    assert response.json()["detail"] == "Database error"