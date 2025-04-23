import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

# Mock HuggingFaceEndpoint before importing main to avoid API token error
with patch("langchain_huggingface.HuggingFaceEndpoint", MagicMock()) as mock_hf_endpoint:
    mock_hf_endpoint.return_value = MagicMock()
    mock_hf_endpoint.return_value.predict.return_value = "mocked response"
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from main import app
    from models.university import University
    from routes import topuni

client = TestClient(app)

# Fake universities for testing
fake_universities = [
    University(id=1, name="Stanford University", departments=["Computer Science", "Engineering"], total_members=500),
    University(id=2, name="MIT", departments=["Physics", "Mathematics"], total_members=450),
    University(id=3, name="Harvard", departments=["Law", "Business"], total_members=400),
    University(id=4, name="Caltech", departments=["Physics", "Chemistry"], total_members=350),
    University(id=5, name="Princeton", departments=["Mathematics", "Literature"], total_members=300),
]

@pytest.fixture
def override_dependencies(monkeypatch):
    mock_db = MagicMock(spec=Session)

    # Mock database operations
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None

    # Mock queries for the default case
    mock_uni_query = MagicMock()
    mock_uni_query.order_by.return_value.limit.return_value.all.return_value = fake_universities

    mock_db.query.side_effect = lambda model: (
        mock_uni_query if model == University else
        MagicMock()
    )

    # Create a generator function that yields our mock db
    def mock_get_db():
        yield mock_db

    # Override the get_db dependency from the router
    app.dependency_overrides[topuni.get_db] = mock_get_db

    yield mock_db

    app.dependency_overrides.clear()

def test_get_top_universities(override_dependencies):
    mock_db = override_dependencies

    # Mock Universities query
    mock_uni_query = MagicMock()
    mock_uni_query.order_by.return_value.limit.return_value.all.return_value = fake_universities
    mock_db.query.side_effect = lambda model: (
        mock_uni_query if model == University else
        MagicMock()
    )

    # Send request to get top universities
    response = client.get("/top/top-universities?limit=5")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    assert data[0]["name"] == "Stanford University"
    assert data[0]["total_members"] == 500
    assert "Computer Science" in data[0]["departments"]
    assert data[1]["name"] == "MIT"
    assert data[4]["name"] == "Princeton"

def test_get_top_universities_custom_limit(override_dependencies):
    mock_db = override_dependencies

    # Mock Universities query with custom limit
    mock_uni_query = MagicMock()
    mock_uni_query.order_by.return_value.limit.return_value.all.return_value = fake_universities[:3]
    mock_db.query.side_effect = lambda model: (
        mock_uni_query if model == University else
        MagicMock()
    )

    # Send request to get top universities with custom limit
    response = client.get("/top/top-universities?limit=3")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["name"] == "Stanford University"
    assert data[1]["name"] == "MIT"
    assert data[2]["name"] == "Harvard"

def test_get_top_universities_empty_result(override_dependencies):
    mock_db = override_dependencies

    # Mock Universities query with empty result
    mock_uni_query = MagicMock()
    mock_uni_query.order_by.return_value.limit.return_value.all.return_value = []
    mock_db.query.side_effect = lambda model: (
        mock_uni_query if model == University else
        MagicMock()
    )

    # Send request to get top universities
    response = client.get("/top/top-universities")
    
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "University not found"

def test_get_top_universities_server_error(override_dependencies):
    mock_db = override_dependencies

    # Mock Universities query to raise an exception
    mock_uni_query = MagicMock()
    mock_uni_query.order_by.return_value.limit.return_value.all.side_effect = Exception("Database error")
    mock_db.query.side_effect = lambda model: (
        mock_uni_query if model == University else
        MagicMock()
    )

    # Send request to get top universities
    response = client.get("/top/top-universities")
    
    assert response.status_code == 500
    data = response.json()
    assert "Internal server error" in data["detail"]
