import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from io import BytesIO
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from models.user import User
from models.research_paper import ResearchPaper
from models.research_collaboration import ResearchCollaboration
from core.dependencies import get_db
from api.v1.endpoints.auth import get_current_user
from main import app



client = TestClient(app)

fake_user = User(id=1, username="testuser", email="test@example.com", fields_of_interest="AI, Machine Learning")

@pytest.fixture(autouse=True)
def override_dependencies(monkeypatch):
    mock_session = MagicMock()

    def _get_db():
        return mock_session

    def _get_user():
        return fake_user

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_current_user] = _get_user

    yield mock_session
    app.dependency_overrides.clear()

# --- TESTS ---

@patch('api.v1.endpoints.research.save_uploaded_research_paper')
def test_upload_paper_success(mock_save, override_dependencies):
    mock_save.return_value = "uploads/paper.pdf"
    file_data = BytesIO(b"Fake PDF")
    response = client.post(
        "/research/upload-paper/",
        data={"title": "Test", "author": "Tester", "research_field": "AI"},
        files={"file": ("test.pdf", file_data, "application/pdf")}
    )
    assert response.status_code == 200
    assert "paper_id" in response.json()

# @patch('api.v1.endpoints.research.get_paper_by_id')
# @patch('os.path.getsize')
# def test_download_paper_success(mock_getsize, mock_get_paper, override_dependencies):
#     mock_getsize.return_value = 50 * 1024 * 1024  # 50MB
#     mock_get_paper.return_value = ResearchPaper(
#         id=1,
#         title="Sample Paper",
#         author="Author",
#         research_field="AI",
#         file_path="https://cdn.test.com/paper.pdf",
#         original_filename="paper.pdf",
#         uploader_id=fake_user.id
#     )
#     response = client.get("/research/papers/download/1/")
#     assert response.status_code == 307
#     assert "location" in response.headers

def test_get_my_post_research_papers(override_dependencies):
    mock_paper = ResearchCollaboration(
        id=1,
        title="My Work",
        research_field="AI",
        details="Testing",
        creator_id=fake_user.id
    )

    query_mock = MagicMock()
    query_mock.filter.return_value.all.return_value = [mock_paper]
    override_dependencies.query.return_value = query_mock

    response = client.get("/research/my_post_research_papers/")
    data = response.json()
    assert response.status_code == 200
    assert len(data) > 0
    assert data[0]["title"] == "My Work"

def test_get_other_research_papers(override_dependencies):
    other_user_id = 2
    mock_paper = ResearchCollaboration(
        id=2,
        title="Others' Work",
        research_field="ML",
        details="Details",
        creator_id=other_user_id
    )

    # First call returns list of other papers
    query_mock1 = MagicMock()
    query_mock1.filter.return_value.all.return_value = [mock_paper]

    # Second call returns None (no existing collab)
    query_mock2 = MagicMock()
    query_mock2.filter.return_value.first.return_value = None

    override_dependencies.query.side_effect = [query_mock1, query_mock2]

    response = client.get("/research/post_research_papers_others/")
    data = response.json()
    assert response.status_code == 200
    assert len(data) > 0
    assert data[0]["can_request_collaboration"] is True

def test_request_collaboration_on_own_research(override_dependencies):
    own_paper = ResearchCollaboration(
        id=1,
        title="Self Work",
        research_field="NLP",
        details="Owned",
        creator_id=fake_user.id
    )

    query_mock = MagicMock()
    query_mock.filter.return_value.first.return_value = own_paper
    override_dependencies.query.return_value = query_mock

    response = client.post(
        "/research/request-collaboration/1/",
        data={"message": "Let me join"}
    )
    assert response.status_code == 400
    assert "Cannot request collaboration on your own research." in response.json()["detail"]
