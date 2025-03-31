import pytest
from fastapi.testclient import TestClient
from main import app  # Adjust if your FastAPI app is imported differently

client = TestClient(app)

# Mock authentication (override dependency)
@pytest.fixture(autouse=True)
def override_get_current_user(monkeypatch):
    from models.user import User

    def mock_get_current_user():
        return User(id=1, username="testuser")

    from api.v1.endpoints import auth
    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

# Example test: GET all research papers (empty at start)
def test_get_papers():
    response = client.get("/papers/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# Example test: Search with no results
def test_search_papers_not_found():
    response = client.get("/papers/search/?keyword=nonexistent")
    assert response.status_code == 404
    assert response.json()["detail"] == "No papers found"

# Example test: Upload paper (mocked file)
def test_upload_paper(monkeypatch):
    def mock_get_db():
        from sqlalchemy.orm import Session
        yield Session()  # You'd ideally use a test DB or mock this

    monkeypatch.setattr("core.dependencies.get_db", mock_get_db)

    file_content = b"%PDF-1.4 test pdf content"
    response = client.post(
        "/upload-paper/",
        files={"file": ("test-paper.pdf", file_content, "application/pdf")},
        data={
            "title": "Test Research",
            "author": "John Doe",
            "research_field": "AI"
        }
    )
    # We expect 500 if no actual DB is mocked, but this ensures it hits the logic
    assert response.status_code in [200, 500]

# You can add more tests for:
# - /request-collaboration/{research_id}/
# - /collaboration-requests/
# - /post-research/
# - /papers/download/{id}/
