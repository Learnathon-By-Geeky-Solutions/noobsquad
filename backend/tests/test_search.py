import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
from unittest.mock import MagicMock
from contextlib import contextmanager
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from main import app
from models.post import Post
from models.user import User
from api.v1.endpoints import search

# Create test client
client = TestClient(app)

# Fake user and fake post for testing
fake_user = User(id=1, username="testuser", email="test@example.com")

fake_post = Post(
    id=1,
    user_id=1,
    content="This is a test post containing keyword",
    post_type="text",
    created_at=datetime.now(),
    like_count=5,
    event=None,
    user=fake_user
)

# ✅ Fixture to override dependencies for all tests
@pytest.fixture(autouse=True)
def override_dependencies(monkeypatch):
    mock_session = MagicMock(spec=Session)

    def _get_db_override():
        return mock_session

    def _get_current_user_override():
        return fake_user

    app.dependency_overrides[search.get_db] = _get_db_override
    app.dependency_overrides[search.get_current_user] = _get_current_user_override

    yield mock_session

    app.dependency_overrides.clear()

# ✅ Test when posts are matched
def test_search_posts_with_match(override_dependencies):
    mock_session = override_dependencies

    mock_query = MagicMock()
    mock_query.filter.return_value.all.return_value = [fake_post]
    mock_session.query.return_value = mock_query

    response = client.get("/search/search", params={"keyword": "keyword"})
    assert response.status_code == 200
    data = response.json()
    assert "posts" in data
    assert len(data["posts"]) == 1
    assert data["posts"][0]["id"] == fake_post.id
    assert data["posts"][0]["content"] == fake_post.content

# ✅ Test when no posts are matched
def test_search_posts_no_match(override_dependencies):
    mock_session = override_dependencies

    mock_query = MagicMock()
    mock_query.filter.return_value.all.return_value = []
    mock_session.query.return_value = mock_query

    response = client.get("/search/search", params={"keyword": "nomatch"})
    assert response.status_code == 200
    assert response.json() == {"posts": []}

# ✅ Test when an internal server error occurs
def test_search_posts_internal_error():
    @contextmanager
    def raise_db_exception():
        raise Exception("DB Error")
        yield

    app.dependency_overrides[search.get_db] = raise_db_exception
    app.dependency_overrides[search.get_current_user] = lambda: fake_user

    response = client.get("/search/search", params={"keyword": "anything"})
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"

    app.dependency_overrides.clear()
