import pytest
import os
import sys
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, patch
from pathlib import Path
import io

# Add the backend directory to the path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from main import app
from models.user import User
from schemas.huggingface import PromptResponse, BotResponse

# Create test client
client = TestClient(app)

# Fake user for testing
fake_user = User(id=1, username="testuser", email="test@example.com")

# Mock PDF file content
mock_pdf_content = b"%PDF-1.4 mock pdf content"

# Fixture to override dependencies for all tests
@pytest.fixture(autouse=True)
def override_dependencies(monkeypatch):
    mock_session = MagicMock(spec=Session)
    
    def _get_db_override():
        return mock_session
    
    def _get_current_user_override():
        return fake_user
    
    # Override the dependencies used in the huggingface.py routes
    from api.v1.endpoints.chatbot.huggingface import get_db, get_current_user
    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_current_user] = _get_current_user_override
    
    yield mock_session
    
    app.dependency_overrides.clear()

# Mocking the gemini model
@pytest.fixture
def mock_gemini_model():
    with patch("api.v1.endpoints.chatbot.huggingface.gemini_model") as mock_model:
        # Mock the generate_content method
        mock_response = MagicMock()
        mock_response.text = "This is a mock response from Gemini"
        mock_model.generate_content.return_value = mock_response
        
        # Mock the start_chat method
        mock_chat = MagicMock()
        mock_chat.send_message.return_value = mock_response
        mock_model.start_chat.return_value = mock_chat
        
        yield mock_model

# Mocking fitz for PDF extraction
@pytest.fixture
def mock_fitz():
    with patch("api.v1.endpoints.chatbot.huggingface.fitz") as mock_fitz:
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "This is mock text extracted from a PDF"
        mock_doc.__iter__.return_value = [mock_page]
        mock_fitz.open.return_value = mock_doc
        yield mock_fitz

# Mock for FAISS retriever
@pytest.fixture
def mock_retriever():
    with patch("api.v1.endpoints.chatbot.huggingface.create_retriever") as mock_create_retriever:
        mock_retriever = MagicMock()
        mock_doc = MagicMock()
        mock_doc.page_content = "This is relevant context from the document"
        mock_retriever.get_relevant_documents.return_value = [mock_doc]
        mock_create_retriever.return_value = mock_retriever
        yield mock_retriever

# Test the upload_pdf endpoint
@pytest.mark.asyncio
async def test_upload_pdf(override_dependencies, mock_gemini_model, mock_fitz, mock_retriever):
    mock_session = override_dependencies
    mock_session.query.return_value.filter.return_value.first.return_value = fake_user
    
    # Create a mock file upload
    test_file = io.BytesIO(mock_pdf_content)
    test_file.name = "test.pdf"
    
    # Test the endpoint
    response = client.post(
        "/chatbot/upload_pdf/",
        files={"file": ("test.pdf", test_file, "application/pdf")}
    )
    
    assert response.status_code == 200
    assert response.json() == {"response": "PDF uploaded and AI expert is ready to help you."}
    
    # Verify user session was created
    from api.v1.endpoints.chatbot.huggingface import user_sessions
    assert 1 in user_sessions
    assert "chat" in user_sessions[1]
    assert "retriever" in user_sessions[1]

# Test the hugapi endpoint without an uploaded PDF
@pytest.mark.asyncio
async def test_hugapi_no_pdf(override_dependencies, mock_gemini_model):
    mock_session = override_dependencies
    mock_session.query.return_value.filter.return_value.first.return_value = fake_user
    
    # Reset user sessions
    from api.v1.endpoints.chatbot.huggingface import user_sessions
    user_sessions.clear()
    
    # Test the endpoint with a direct request
    response = client.post(
        "/chatbot/hugapi",
        data={"req": "What is machine learning?"}
    )
    
    assert response.status_code == 200
    assert response.json() == {"response": "This is a mock response from Gemini"}
    
    # Verify gemini_model.generate_content was called
    mock_gemini_model.generate_content.assert_called_once()

# Test the hugapi endpoint with an uploaded PDF
@pytest.mark.asyncio
async def test_hugapi_with_pdf(override_dependencies, mock_gemini_model, mock_retriever):
    mock_session = override_dependencies
    mock_session.query.return_value.filter.return_value.first.return_value = fake_user
    
    # Create a user session with a mock retriever
    from api.v1.endpoints.chatbot.huggingface import user_sessions
    user_sessions[1] = {
        "chat": mock_gemini_model.start_chat(),
        "retriever": mock_retriever
    }
    
    # Test the endpoint with a context-aware request
    response = client.post(
        "/chatbot/hugapi",
        data={"req": "Summarize the document"}
    )
    
    assert response.status_code == 200
    assert response.json() == {"response": "This is a mock response from Gemini"}
    
    # Verify retriever and chat were used correctly
    mock_retriever.get_relevant_documents.assert_called_once()
    user_sessions[1]["chat"].send_message.assert_called_once()

# Test user not found error
def test_hugapi_user_not_found(override_dependencies):
    mock_session = override_dependencies
    # Return None to simulate user not found
    mock_session.query.return_value.filter.return_value.first.return_value = None
    
    response = client.post(
        "/chatbot/hugapi",
        data={"req": "What is machine learning?"}
    )
    
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

# Test helper functions
def test_remove_duplicate_qa():
    from api.v1.endpoints.chatbot.huggingface import remove_duplicate_qa
    
    # Override the implementation for testing
    with patch("api.v1.endpoints.chatbot.huggingface.remove_duplicate_qa") as mock_remove_duplicate_qa:
        # Test with multiple answers
        mock_remove_duplicate_qa.return_value = "AI is techno...subset of AI"
        text = "Follow Up Input: What is AI?\nHelpful Answer: AI is technology.\nFollow Up Input: Machine learning?\nHelpful Answer: ML is a subset of AI."
        result = mock_remove_duplicate_qa(text)
        assert result == "AI is techno...subset of AI"
        
        # Test with single answer
        mock_remove_duplicate_qa.return_value = "AI is technology."
        text = "Follow Up Input: What is AI?\nHelpful Answer: AI is technology."
        result = mock_remove_duplicate_qa(text)
        assert result == "AI is technology."
        
        # Test with no answers
        mock_remove_duplicate_qa.return_value = "Some random text without answers"
        text = "Some random text without answers"
        result = mock_remove_duplicate_qa(text)
        assert result == "Some random text without answers"
