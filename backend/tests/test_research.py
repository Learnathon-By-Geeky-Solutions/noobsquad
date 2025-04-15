import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from main import app
from models.user import User
from models.research_paper import ResearchPaper
from sqlalchemy.orm import Session
from io import BytesIO
from core.dependencies import get_db
from api.v1.endpoints.auth import get_current_user

# Create a test client
client = TestClient(app)

# Fake user for testing purposes
fake_user = User(id=1, username="testuser", email="test@example.com")

# Mock database and user dependency
@pytest.fixture(autouse=True)
def override_dependencies(monkeypatch):
    mock_session = MagicMock(spec=Session)

    def _get_db_override():
        return mock_session

    def _get_current_user_override():
        return fake_user

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_current_user] = _get_current_user_override

    yield mock_session

    app.dependency_overrides.clear()


# Test uploading a research paper
def test_upload_paper(override_dependencies):
    mock_session = override_dependencies

    # Simulate a file with mock data
    mock_file = BytesIO(b"fake data")  # Simulate file content
    mock_file.name = "test_paper.pdf"  # Simulate file name

    # Ensure that the file upload is correctly handled with form data
    response = client.post(
        "/research/upload-paper/",
        data={
            "title": "Research Paper Title",
            "author": "Author Name",
            "research_field": "Field Name",
        },
        files={"file": ("test_paper.pdf", mock_file, "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Paper uploaded successfully"


# Test fetching research papers
def test_get_papers(override_dependencies):
    mock_session = override_dependencies

    mock_paper = MagicMock(spec=ResearchPaper)
    mock_paper.id = 1
    mock_paper.title = "Research Paper Title"
    mock_paper.author = "Author Name"
    mock_paper.research_field = "Field Name"
    mock_session.query.return_value.all.return_value = [mock_paper]

    response = client.get("/research/papers/")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Research Paper Title"


# Test searching for papers by keyword
def test_search_papers(override_dependencies):
    mock_session = override_dependencies

    mock_paper = MagicMock(spec=ResearchPaper)
    mock_paper.id = 1
    mock_paper.title = "Research Paper Title"
    mock_paper.author = "Author Name"
    mock_paper.research_field = "Field Name"
    mock_session.query.return_value.filter.return_value.all.return_value = [mock_paper]

    response = client.get("/research/papers/search/", params={"keyword": "Research"})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Research Paper Title"


# Test posting research collaboration
def test_post_research(override_dependencies):
    mock_session = override_dependencies

    response = client.post(
        "/research/post-research/",
        data={
            "title": "Collaboration Research Title",
            "research_field": "Field Name",
            "details": "Research Details",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Research work posted successfully"


# Test requesting collaboration on research
def test_request_collaboration(override_dependencies):
    mock_session = override_dependencies

    response = client.post(
        "/research/request-collaboration/1/",
        data={"message": "I want to collaborate on this research."},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Collaboration request sent successfully"
