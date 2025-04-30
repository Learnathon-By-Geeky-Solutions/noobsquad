import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from io import BytesIO
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from main import app
from models.user import User
from models.research_paper import ResearchPaper
from models.research_collaboration import ResearchCollaboration
from models.collaboration_request import CollaborationRequest
from sqlalchemy.orm import Session
from core.dependencies import get_db
from api.v1.endpoints.auth import get_current_user

# Create a test client
client = TestClient(app)

# Mock user for testing
fake_user = User(id=1, username="testuser", email="test@example.com", fields_of_interest="AI, Machine Learning")

@pytest.fixture(autouse=True)
def override_dependencies(monkeypatch):
    mock_session = MagicMock(spec=Session)
    
    # Mock database operations
    mock_session.add.return_value = None
    mock_session.commit.return_value = None
    mock_session.refresh.return_value = None
    
    # Mock query behaviors for common operations
    def get_query_mock(model):
        mock_query = MagicMock()
        if model == ResearchPaper:
            mock_query.filter.return_value.first.return_value = None
            mock_query.filter.return_value.all.return_value = []
        elif model == ResearchCollaboration:
            mock_query.filter.return_value.first.return_value = None
        return mock_query
    
    mock_session.query.side_effect = get_query_mock
    
    def _get_db_override():
        return mock_session
    
    def _get_current_user_override():
        return fake_user
    
    # Override dependencies
    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_current_user] = _get_current_user_override
    
    yield mock_session
    
    # Clear overrides after test
    app.dependency_overrides.clear()

# Test uploading paper with empty fields
@patch('api.v1.endpoints.research.validate_file_extension')
@patch('api.v1.endpoints.research.save_uploaded_research_paper')
def test_upload_paper_empty_fields(mock_save_paper, mock_validate_ext, override_dependencies):
    mock_session = override_dependencies
    mock_validate_ext.return_value = ".pdf"
    mock_save_paper.return_value = "path/to/saved/paper.pdf"
    mock_file = BytesIO(b"fake data")
    
    # Test empty title
    response = client.post(
        "/research/upload-paper/",
        data={
            "title": "",
            "author": "Author Name",
            "research_field": "Field Name",
        },
        files={"file": ("test_paper.pdf", mock_file, "application/pdf")},
    )
    assert response.status_code == 422  # Validation error

    # Test empty author
    response = client.post(
        "/research/upload-paper/",
        data={
            "title": "Paper Title",
            "author": "",
            "research_field": "Field Name",
        },
        files={"file": ("test_paper.pdf", mock_file, "application/pdf")},
    )
    assert response.status_code == 422  # Validation error

# Test recommendation algorithm with no matching papers
def test_get_recommended_papers_no_matches(override_dependencies):
    mock_session = override_dependencies
    
    # Mock user profile query
    mock_profile = MagicMock()
    mock_profile.fields_of_interest = "UnmatchedField1,UnmatchedField2"
    mock_session.query.return_value.filter.return_value.first.return_value = mock_profile
    
    # Mock papers query for both interest-based and additional papers
    mock_papers_query = MagicMock()
    mock_papers_query.filter.return_value.limit.return_value.all.return_value = []
    mock_session.query.return_value = mock_papers_query
    
    response = client.get("/research/recommended/")
    
    assert response.status_code == 200
    assert len(response.json()) == 0

# Test unauthorized collaboration request
def test_request_collaboration_unauthorized(override_dependencies):
    mock_session = override_dependencies
    mock_session.query.return_value = MagicMock(
        filter=lambda *args: MagicMock(first=lambda: None)
    )
    
    # Mock an unauthorized user (no token)
    app.dependency_overrides[get_current_user] = lambda: None
    
    response = client.post(
        "/research/request-collaboration/1/",
        data={"message": "Collaboration request"},
    )
    
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]
    
    # Reset the override
    app.dependency_overrides.clear()

# Test collaboration request on non-existent research
def test_request_collaboration_not_found(override_dependencies):
    mock_session = override_dependencies
    mock_session.query.return_value = MagicMock(
        filter=lambda *args: MagicMock(first=lambda: None)
    )
    
    # Mock the database query to return None (research not found)
    query_mock = MagicMock()
    filter_mock = MagicMock()
    filter_mock.first.return_value = None
    query_mock.filter.return_value = filter_mock
    mock_session.query.return_value = query_mock
    
    response = client.post(
        "/research/request-collaboration/999/",
        data={"message": "Collaboration request"},
    )
    
    assert response.status_code == 404
    assert "Research work not found" in response.json()["detail"]

# Test paper download size limit
@patch('api.v1.endpoints.research.get_paper_by_id')
def test_download_paper_size_limit(mock_get_paper, override_dependencies):
    mock_session = override_dependencies
    mock_session.query.return_value = MagicMock(
        filter=lambda *args: MagicMock(first=lambda: MagicMock(id=1, file_path="path/to/large_paper.pdf"))
    )
    
    # Create a mock paper with large file size
    mock_paper = MagicMock(spec=ResearchPaper)
    mock_paper.id = 1
    mock_paper.file_path = "path/to/large_paper.pdf"
    mock_get_paper.return_value = mock_paper
    
    # Mock file size check
    with patch('os.path.getsize') as mock_size:
        mock_size.return_value = 1024 * 1024 * 101  # 101MB (over 100MB limit)
        
        response = client.get("/research/papers/download/1/")
        
        assert response.status_code == 400
        assert "File too large" in response.json()["detail"]

# Test malformed research field
def test_post_research_malformed_field(override_dependencies):
    mock_session = override_dependencies
    
    # Create a validator function
    def validate_research_field(field: str) -> bool:
        import re
        return bool(re.match(r'^[a-zA-Z0-9\s,]+$', field))
    
    response = client.post(
        "/research/post-research/",
        data={
            "title": "Research Title",
            "research_field": "!@#$%^&*()",  # Invalid characters
            "details": "Research Details"
        }
    )
    
    assert response.status_code == 422
    assert "Invalid research field" in response.json()["detail"]

# Test paper search with special characters
def test_search_papers_special_chars(override_dependencies):
    mock_session = override_dependencies
    
    # Mock search query to return no results
    mock_query = MagicMock()
    mock_query.filter.return_value.all.return_value = []
    mock_session.query.return_value = mock_query
    
    response = client.get("/research/papers/search/", params={"keyword": "SQL; DROP TABLE papers;"})
    
    assert response.status_code == 404  # API returns 404 when no papers found
    assert "No papers found" in response.json()["detail"]