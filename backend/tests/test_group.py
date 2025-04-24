import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, patch
from collections import defaultdict
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

# Import the app
from main import app
from models.university import University
from models.user import User
from models.post import Post
from core.dependencies import get_db

# Create test client
client = TestClient(app)

# Fake university data
@pytest.fixture
def fake_universities():
    return [
        University(
            id=1,
            name="TestUniversity",
            departments=["Computer Science", "Mathematics", "Physics", "Chemistry"],
            total_members=10
        ),
        University(
            id=2,
            name="AnotherUniversity",
            departments=["Biology", "Psychology", "Economics"],
            total_members=8
        )
    ]

# Fake user data
@pytest.fixture
def fake_users():
    return [
        User(
            id=1,
            username="user1",
            email="user1@example.com",
            university_name="TestUniversity",
            department="Computer Science"
        ),
        User(
            id=2,
            username="user2",
            email="user2@example.com",
            university_name="TestUniversity",
            department="Computer Science"
        ),
        User(
            id=3,
            username="user3",
            email="user3@example.com",
            university_name="TestUniversity",
            department="Mathematics"
        )
    ]

# Fake post data
@pytest.fixture
def fake_posts():
    return [
        Post(
            id=1,
            user_id=1,
            content="This is a post about #testuniversity",
            created_at="2023-01-01T12:00:00"
        ),
        Post(
            id=2,
            user_id=2,
            content="Another post with #testuniversity hashtag",
            created_at="2023-01-02T12:00:00"
        ),
        Post(
            id=3,
            user_id=3,
            content="Mathematics post #testuniversity",
            created_at="2023-01-03T12:00:00"
        )
    ]

# Fixture to override dependencies
@pytest.fixture
def mock_db():
    mock_session = MagicMock(spec=Session)
    
    # Store the original dependency
    original_get_db = app.dependency_overrides.get(get_db)
    
    # Override get_db dependency
    app.dependency_overrides[get_db] = lambda: mock_session
    
    # Also override the local get_db in the group router
    from routes.group import get_db as local_get_db
    original_local_get_db = app.dependency_overrides.get(local_get_db)
    app.dependency_overrides[local_get_db] = lambda: mock_session
    
    yield mock_session
    
    # Restore original dependencies or clear overrides
    if original_get_db:
        app.dependency_overrides[get_db] = original_get_db
    else:
        app.dependency_overrides.pop(get_db, None)
        
    if original_local_get_db:
        app.dependency_overrides[local_get_db] = original_local_get_db
    else:
        app.dependency_overrides.pop(local_get_db, None)

# Test getting university info
def test_get_university_info(mock_db, fake_users, fake_posts):
    # Setup mock responses
    # First query returns users
    mock_users_query = MagicMock()
    mock_users_query.filter.return_value.all.return_value = fake_users
    
    # Second query returns posts
    mock_posts_query = MagicMock()
    mock_posts_query.filter.return_value.order_by.return_value.all.return_value = fake_posts
    
    # Configure mock_db to return different query objects
    mock_db.query.side_effect = [mock_users_query, mock_posts_query]
    
    # Send GET request
    response = client.get("/universities/TestUniversity")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["university"] == "TestUniversity"
    assert data["total_members"] == 3
    # Check departments structure as a dictionary
    assert len(data["departments"]) == 2  # Computer Science and Mathematics
    assert "Computer Science" in data["departments"]
    assert isinstance(data["departments"]["Computer Science"], list)
    assert len(data["departments"]["Computer Science"]) > 0
    assert len(data["post_ids"]) == 3

# Test getting all universities
def test_get_universities(mock_db, fake_universities):
    # Mock university query to return all universities
    mock_uni_query = MagicMock()
    mock_uni_query.all.return_value = fake_universities
    mock_db.query.return_value = mock_uni_query
    
    # Send GET request
    response = client.get("/universities/?limit_departments=2")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "TestUniversity"
    assert len(data[0]["departments"]) == 2
    assert data[0]["has_more_departments"] is True

# Test getting all departments
def test_get_all_departments(mock_db, fake_universities):
    # Mock university query to return a specific university
    mock_uni_query = MagicMock()
    mock_uni_query.filter.return_value.first.return_value = fake_universities[0]
    mock_db.query.return_value = mock_uni_query
    
    # Send GET request
    response = client.get("/universities/1/departments")
    
    # Assertions
    assert response.status_code == 200
    departments = response.json()
    assert len(departments) == 4
    assert "Computer Science" in departments
    assert "Mathematics" in departments

# Test getting all departments - not found case
def test_get_all_departments_not_found(mock_db):
    # Mock university query to return None
    mock_uni_query = MagicMock()
    mock_uni_query.filter.return_value.first.return_value = None
    mock_db.query.return_value = mock_uni_query
    
    # Send GET request
    response = client.get("/universities/999/departments")
    
    # Assertions
    assert response.status_code == 404
    assert response.json()["detail"] == "University not found"

# Test getting post IDs by department
def test_get_post_ids_by_department(mock_db, fake_users, fake_posts):
    # Filter only Computer Science users
    cs_users = [user for user in fake_users if user.department == "Computer Science"]
    
    # Mock queries
    mock_users_query = MagicMock()
    mock_users_query.filter.return_value.all.return_value = cs_users
    
    mock_posts_query = MagicMock()
    mock_posts_query.filter.return_value.order_by.return_value.all.return_value = fake_posts[:2]
    
    # Configure mock_db
    mock_db.query.side_effect = [mock_users_query, mock_posts_query]
    
    # Send GET request
    response = client.get("/universities/posts/university/TestUniversity/department/Computer%20Science")
    
    # Assertions
    assert response.status_code == 200
    post_ids = response.json()
    assert len(post_ids) == 2
    assert 1 in post_ids
    assert 2 in post_ids

# Test getting empty post IDs by department
def test_get_post_ids_by_department_no_users(mock_db):
    # Mock user query to return empty list
    mock_user_query = MagicMock()
    mock_user_query.filter.return_value.all.return_value = []
    mock_db.query.return_value = mock_user_query
    
    # Send GET request
    response = client.get("/universities/posts/university/TestUniversity/department/NonExistentDepartment")
    
    # Assertions
    assert response.status_code == 200
    assert response.json() == []

# Test getting posts by hashtag
def test_get_posts_by_hashtag(mock_db):
    # Mock post_hashtags query
    mock_hashtag_query = MagicMock()
    mock_hashtag_query.all.return_value = [(1,), (2,), (3,)]
    
    # Mock posts query for sorting
    mock_posts_query = MagicMock()
    mock_posts_query.filter.return_value.order_by.return_value.all.return_value = [(3,), (2,), (1,)]
    
    # Configure mock_db
    mock_db.query.side_effect = [mock_hashtag_query, mock_posts_query]
    
    # Send GET request
    response = client.get("/universities/posts/by-hashtag")
    
    # Assertions
    assert response.status_code == 200
    post_ids = response.json()
    assert len(post_ids) == 3
    assert post_ids == [3, 2, 1]  # Sorted by created_at desc

# Test empty result for posts by hashtag
def test_get_posts_by_hashtag_no_posts(mock_db):
    # Mock queries to return empty results
    mock_empty_query = MagicMock()
    mock_empty_query.all.return_value = []
    
    mock_posts_query = MagicMock()
    mock_posts_query.filter.return_value.order_by.return_value.all.return_value = []
    
    # Configure mock_db
    mock_db.query.side_effect = [mock_empty_query, mock_posts_query]
    
    # Send GET request
    response = client.get("/universities/posts/by-hashtag")
    
    # Assertions
    assert response.status_code == 200
    assert response.json() == []