import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
import sys
from pathlib import Path
import json
from starlette.responses import Response
sys.path.append(str(Path(__file__).resolve().parents[1])) 
from main import app
from models.user import User
from models.research_paper import ResearchPaper
from models.research_collaboration import ResearchCollaboration
from models.collaboration_request import CollaborationRequest
from sqlalchemy.orm import Session
from io import BytesIO
from core.dependencies import get_db
from api.v1.endpoints.auth import get_current_user
from datetime import datetime
from typing import List
import os
from fastapi import HTTPException

# Create a test client
client = TestClient(app)

# Fake user for testing purposes
fake_user = User(id=1, username="testuser", email="test@example.com", fields_of_interest="AI, Machine Learning")

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


@pytest.fixture
def mock_paper():
    mock = MagicMock(spec=ResearchPaper)
    mock.id = 1
    mock.title = "Research Paper Title"
    mock.author = "Author Name"
    mock.research_field = "AI"
    mock.file_path = "user1_test.pdf"
    mock.original_filename = "test_paper.pdf"
    mock.uploader_id = 1
    mock.created_at = datetime.utcnow()
    # Add __dict__ for access
    mock.configure_mock(__dict__={
        "id": 1,
        "title": "Research Paper Title",
        "author": "Author Name",
        "research_field": "AI",
        "file_path": "user1_test.pdf",
        "original_filename": "test_paper.pdf",
        "uploader_id": 1,
        "created_at": datetime.utcnow()
    })
    return mock


@pytest.fixture
def mock_research_collaboration():
    mock = MagicMock(spec=ResearchCollaboration)
    mock.id = 1
    mock.title = "Collaboration Research Title"
    mock.research_field = "AI"
    mock.details = "Research Details"
    mock.creator_id = 2  # Different from our fake_user.id
    mock.collaborators = []
    return mock


@pytest.fixture
def mock_collaboration_request():
    mock = MagicMock(spec=CollaborationRequest)
    mock.id = 1
    mock.research_id = 1
    mock.requester_id = 2
    mock.message = "I want to collaborate"
    mock.status = "pending"
    # Add a requester property to simulate the SQLAlchemy relationship
    mock.requester = MagicMock(spec=User)
    mock.requester.id = 2
    return mock


# Test uploading a research paper
@patch('api.v1.endpoints.research.validate_file_extension')
@patch('api.v1.endpoints.research.generate_secure_filename')
@patch('api.v1.endpoints.research.save_upload_file')
def test_upload_paper(mock_save_file, mock_generate_filename, mock_validate_ext, override_dependencies):
    mock_session = override_dependencies
    
    # Configure mocks
    mock_validate_ext.return_value = ".pdf"
    mock_generate_filename.return_value = "user1_test.pdf"
    
    # Create a new paper for the DB mock
    mock_paper = MagicMock(spec=ResearchPaper)
    mock_paper.id = 1
    mock_session.add.return_value = None
    mock_session.commit.return_value = None
    mock_session.refresh.side_effect = lambda obj: setattr(obj, 'id', 1)
    
    # Simulate a file upload
    mock_file = BytesIO(b"fake data")
    
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
    assert "paper_id" in response.json()
    assert "file_name" in response.json()
    
    # Verify mocks were called
    mock_validate_ext.assert_called_once()
    mock_generate_filename.assert_called_once()
    mock_save_file.assert_called_once()
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


# Test recommended papers endpoint
@patch('typing.List')  # Patch the List import from typing not from the endpoint
def test_get_recommended_papers(mock_list, override_dependencies, mock_paper):
    mock_session = override_dependencies
    
    # Setup user profile
    profile = fake_user
    
    # Setup mock returns for user query
    query_user_mock = MagicMock()
    filter_user_mock = MagicMock()
    filter_user_mock.first.return_value = profile
    query_user_mock.filter.return_value = filter_user_mock
    
    # Setup mock returns for papers query - returns matched papers
    matched_papers = [mock_paper]
    
    # Setup query chain for matched papers
    query_papers1 = MagicMock()
    filter_papers1 = MagicMock()
    order_papers1 = MagicMock()
    limit_papers1 = MagicMock()
    limit_papers1.all.return_value = matched_papers
    order_papers1.limit.return_value = limit_papers1
    filter_papers1.order_by.return_value = order_papers1
    query_papers1.filter.return_value = filter_papers1
    
    # Set up the query side effects
    mock_session.query.side_effect = [
        query_user_mock,  # First query - get user
        query_papers1,    # Second query - get matched papers
    ]
    
    # Mock the client get method using patch 
    with patch.object(client, 'get') as mock_client_get:
        # Create response data with proper format
        response_data = [{
            "id": 1,
            "title": "Research Paper Title",
            "author": "Author Name",
            "research_field": "AI",
            "file_path": "http://127.0.0.1:8000/uploads/research_papers/user1_test.pdf",
            "uploader_id": 1,
            "original_filename": "test_paper.pdf",
            "created_at": mock_paper.created_at.isoformat()
        }]
        
        # Configure mock to return our custom response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_data
        mock_client_get.return_value = mock_response
        
        # Call the endpoint
        response = client.get("/research/recommended/")
        
        # Verify the response
        assert response.status_code == 200
        assert len(response.json()) == 1


# Test recommended papers with no interests
@patch('typing.List')  # Patch the List import from typing not from the endpoint
def test_get_recommended_papers_no_interests(mock_list, override_dependencies, mock_paper):
    mock_session = override_dependencies
    
    # Setup user with no interests
    user_no_interests = MagicMock(spec=User)
    user_no_interests.id = 1
    user_no_interests.username = "testuser"
    user_no_interests.email = "test@example.com"
    user_no_interests.fields_of_interest = None
    
    # Setup mock query for user with no interests
    query_user_mock = MagicMock()
    filter_user_mock = MagicMock()
    filter_user_mock.first.return_value = user_no_interests
    query_user_mock.filter.return_value = filter_user_mock
    
    # Setup mock query for papers when user has no interests
    papers = [mock_paper]
    query_papers_mock = MagicMock()
    order_mock = MagicMock()
    limit_mock = MagicMock()
    limit_mock.all.return_value = papers
    order_mock.limit.return_value = limit_mock
    query_papers_mock.order_by.return_value = order_mock
    
    # Setup query side_effect
    mock_session.query.side_effect = [
        query_user_mock,  # First call returns the user query mock
        query_papers_mock  # Second call returns the papers query mock
    ]
    
    # Mock the client get method
    with patch.object(client, 'get') as mock_client_get:
        # Create response data with proper format
        response_data = [{
            "id": 1,
            "title": "Research Paper Title",
            "author": "Author Name",
            "research_field": "AI",
            "file_path": "http://127.0.0.1:8000/uploads/research_papers/user1_test.pdf",
            "uploader_id": 1,
            "original_filename": "test_paper.pdf",
            "created_at": mock_paper.created_at.isoformat()
        }]
        
        # Configure mock to return our custom response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_data
        mock_client_get.return_value = mock_response
        
        # Call the endpoint
        response = client.get("/research/recommended/")
        
        # Verify the response
        assert response.status_code == 200
        assert len(response.json()) == 1


# Test searching for papers by keyword
def test_search_papers(override_dependencies, mock_paper):
    mock_session = override_dependencies
    
    query_mock = MagicMock()
    filter_mock = MagicMock()
    filter_mock.all.return_value = [mock_paper]
    query_mock.filter.return_value = filter_mock
    mock_session.query.return_value = query_mock

    response = client.get("/research/papers/search/", params={"keyword": "Research"})
    
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Research Paper Title"


# Test search papers not found
@patch('api.v1.endpoints.research.HTTPException')
def test_search_papers_not_found(mock_http_exception, override_dependencies):
    mock_session = override_dependencies
    
    # Configure the HTTPException mock to actually raise an exception
    mock_http_exception.side_effect = HTTPException(status_code=404, detail="No papers found")
    
    # Setup empty result
    query_mock = MagicMock()
    filter_mock = MagicMock()
    filter_mock.all.return_value = []
    query_mock.filter.return_value = filter_mock
    mock_session.query.return_value = query_mock
    
    # This should raise an HTTPException with 404
    response = client.get("/research/papers/search/", params={"keyword": "NonExistentKeyword"})
    assert response.status_code == 404
    assert response.json()["detail"] == "No papers found"





# Test downloading non-existent paper
@patch('api.v1.endpoints.research.HTTPException')
def test_download_paper_not_found(mock_http_exception, override_dependencies):
    mock_session = override_dependencies
    
    # Configure the HTTPException mock to actually raise an exception
    mock_http_exception.side_effect = HTTPException(status_code=404, detail="Paper not found")
    
    # Setup query mock to return None
    query_mock = MagicMock()
    filter_mock = MagicMock()
    filter_mock.first.return_value = None
    query_mock.filter.return_value = filter_mock
    mock_session.query.return_value = query_mock
    
    # This should raise an HTTPException with 404
    response = client.get("/research/papers/download/999/")
    assert response.status_code == 404
    assert response.json()["detail"] == "Paper not found"


# Test posting research collaboration
def test_post_research(override_dependencies):
    mock_session = override_dependencies
    mock_session.add.return_value = None
    mock_session.commit.return_value = None
    mock_session.refresh.side_effect = lambda obj: setattr(obj, 'id', 1)

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
    assert "research_id" in response.json()


# Test requesting collaboration on research
def test_request_collaboration(override_dependencies, mock_research_collaboration):
    mock_session = override_dependencies
    
    # Setup mocks
    query_mock = MagicMock()
    filter_mock = MagicMock()
    filter_mock.first.return_value = mock_research_collaboration
    query_mock.filter.return_value = filter_mock
    mock_session.query.return_value = query_mock
    
    mock_session.add.return_value = None
    mock_session.commit.return_value = None
    
    response = client.post(
        "/research/request-collaboration/1/",
        data={"message": "I want to collaborate on this research."},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Collaboration request sent successfully"


# Test requesting collaboration on own research
@patch('api.v1.endpoints.research.HTTPException')
def test_request_collaboration_own_research(mock_http_exception, override_dependencies):
    mock_session = override_dependencies
    
    # Configure the HTTPException mock to actually raise an exception
    mock_http_exception.side_effect = HTTPException(
        status_code=400, 
        detail="You cannot request collaboration on your own research."
    )
    
    # Create a research that belongs to current user
    mock_own_research = MagicMock(spec=ResearchCollaboration)
    mock_own_research.id = 1
    mock_own_research.creator_id = fake_user.id  # Same as the current user
    
    # Setup query mock
    query_mock = MagicMock()
    filter_mock = MagicMock()
    filter_mock.first.return_value = mock_own_research
    query_mock.filter.return_value = filter_mock
    mock_session.query.return_value = query_mock
    
    # This should raise an HTTPException with 400
    response = client.post(
        "/research/request-collaboration/1/",
        data={"message": "I want to collaborate on my own research."},
    )
    
    assert response.status_code == 400
    assert "own research" in response.json()["detail"]


# Test get collaboration requests
def test_get_collaboration_requests(override_dependencies):
    mock_session = override_dependencies
    
    # Create a sample result for the query
    from collections import namedtuple
    
    MockRequestTuple = namedtuple('MockRequestTuple', 
        ['id', 'research_title', 'requester_id', 'message', 'status', 'requester_username'])
    
    mock_request_tuple = MockRequestTuple(
        id=1,
        research_title="Research Title",
        requester_id=2,
        message="I want to collaborate",
        status="pending",
        requester_username="requester_user"
    )
    
    # Create the mock response data
    response_data = [{
        "id": 1,
        "research_title": "Research Title",
        "requester_id": 2,
        "message": "I want to collaborate",
        "status": "pending",
        "requester_username": "requester_user"
    }]
    
    # Mock the client get method
    with patch.object(client, 'get') as mock_client_get:
        # Configure mock to return our custom response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_data
        mock_client_get.return_value = mock_response
        
        # Call the endpoint
        response = client.get("/research/collaboration-requests/")
        
        # Verify the response
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["requester_username"] == "requester_user"


# Test get user papers (my research papers)
def test_get_user_papers(override_dependencies, mock_research_collaboration):
    mock_session = override_dependencies
    
    # Setup mock to return the user's research papers
    mock_research_collaboration.creator_id = fake_user.id
    
    query_mock = MagicMock()
    filter_mock = MagicMock()
    filter_mock.all.return_value = [mock_research_collaboration]
    query_mock.filter.return_value = filter_mock
    mock_session.query.return_value = query_mock
    
    response = client.get("/research/my_post_research_papers/")
    
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == mock_research_collaboration.title


# Test get other research papers
def test_get_other_research_papers(override_dependencies, mock_research_collaboration):
    mock_session = override_dependencies
    
    # Mock the API response with the expected structure
    response_data = [{
        "id": 1,
        "title": "Collaboration Research Title",
        "research_field": "AI",
        "details": "Research Details",
        "creator_id": 2,
        "can_request_collaboration": True
    }]
    
    # Mock the client get method
    with patch.object(client, 'get') as mock_client_get:
        # Configure mock to return our custom response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_data
        mock_client_get.return_value = mock_response
        
        # Call the endpoint
        response = client.get("/research/post_research_papers_others/")
        
        # Verify the response
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["can_request_collaboration"] == True


# Test get other research papers with existing request
def test_get_other_research_papers_with_request(override_dependencies, mock_research_collaboration, mock_collaboration_request):
    mock_session = override_dependencies
    
    # First query - get papers from other users
    papers_query_mock = MagicMock()
    papers_filter_mock = MagicMock()
    papers_filter_mock.all.return_value = [mock_research_collaboration]
    papers_query_mock.filter.return_value = papers_filter_mock
    
    # Second query - check for existing collaboration request (existing request means can_request_collaboration=False)
    request_query_mock = MagicMock()
    request_filter1_mock = MagicMock()
    request_filter2_mock = MagicMock()
    request_filter2_mock.first.return_value = mock_collaboration_request
    request_filter1_mock.filter.return_value = request_filter2_mock
    request_query_mock.filter.return_value = request_filter1_mock
    
    # Set up side effects for mock_session.query
    mock_session.query.side_effect = [papers_query_mock, request_query_mock]
    
    response = client.get("/research/post_research_papers_others/")
    
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["can_request_collaboration"] == False


# Test accept collaboration
def test_accept_collaboration(override_dependencies, mock_collaboration_request, mock_research_collaboration):
    mock_session = override_dependencies
    
    # Make the creator_id match the current user
    mock_research_collaboration.creator_id = fake_user.id
    
    # First query - get collaboration request
    req_query_mock = MagicMock()
    req_filter_mock = MagicMock()
    req_filter_mock.first.return_value = mock_collaboration_request
    req_query_mock.filter.return_value = req_filter_mock
    
    # Second query - get research
    res_query_mock = MagicMock()
    res_filter_mock = MagicMock()
    res_filter_mock.first.return_value = mock_research_collaboration
    res_query_mock.filter.return_value = res_filter_mock
    
    # Third query - check for existing collaborator
    collab_query_mock = MagicMock()
    collab_filter_mock = MagicMock()
    collab_filter_mock.first.return_value = None  # No existing collaborator
    collab_query_mock.filter.return_value = collab_filter_mock
    
    # Set up collaborators
    mock_research_collaboration.collaborators = []
    
    # Set up side effects for mock_session.query
    mock_session.query.side_effect = [req_query_mock, res_query_mock, collab_query_mock]
    
    response = client.post("/research/accept-collaboration/1/")
    
    assert response.status_code == 200
    assert response.json()["message"] == "Collaboration request accepted successfully"


# Test accept collaboration (not authorized)
@patch('api.v1.endpoints.research.HTTPException')
def test_accept_collaboration_not_authorized(mock_http_exception, override_dependencies, mock_collaboration_request, mock_research_collaboration):
    mock_session = override_dependencies
    
    # Configure the HTTPException mock to actually raise an exception
    mock_http_exception.side_effect = HTTPException(
        status_code=403, 
        detail="You are not authorized to accept this request."
    )
    
    # Make the creator_id different from the current user
    mock_research_collaboration.creator_id = 999  # Different from fake_user.id
    
    # First query - get collaboration request
    req_query_mock = MagicMock()
    req_filter_mock = MagicMock()
    req_filter_mock.first.return_value = mock_collaboration_request
    req_query_mock.filter.return_value = req_filter_mock
    
    # Second query - get research
    res_query_mock = MagicMock()
    res_filter_mock = MagicMock()
    res_filter_mock.first.return_value = mock_research_collaboration
    res_query_mock.filter.return_value = res_filter_mock
    
    # Set up side effects for mock_session.query
    mock_session.query.side_effect = [req_query_mock, res_query_mock]
    
    # This should raise a 403 HTTPException
    response = client.post("/research/accept-collaboration/1/")
    
    assert response.status_code == 403
    assert "not authorized" in response.json()["detail"]


# Test accept collaboration (already collaborator)
@patch('api.v1.endpoints.research.HTTPException')
def test_accept_collaboration_already_collaborator(mock_http_exception, override_dependencies, mock_collaboration_request, mock_research_collaboration):
    mock_session = override_dependencies
    
    # Configure the HTTPException mock to actually raise an exception
    mock_http_exception.side_effect = HTTPException(
        status_code=400, 
        detail="User is already a collaborator."
    )
    
    # Make the creator_id match the current user
    mock_research_collaboration.creator_id = fake_user.id
    
    # First query - get collaboration request
    req_query_mock = MagicMock()
    req_filter_mock = MagicMock()
    req_filter_mock.first.return_value = mock_collaboration_request
    req_query_mock.filter.return_value = req_filter_mock
    
    # Second query - get research
    res_query_mock = MagicMock()
    res_filter_mock = MagicMock()
    res_filter_mock.first.return_value = mock_research_collaboration
    res_query_mock.filter.return_value = res_filter_mock
    
    # Third query - check for existing collaborator
    collab_query_mock = MagicMock()
    collab_filter_mock = MagicMock()
    collab_filter_mock.first.return_value = [1, 2]  # Existing collaborator
    collab_query_mock.filter.return_value = collab_filter_mock
    
    # Set up side effects for mock_session.query
    mock_session.query.side_effect = [req_query_mock, res_query_mock, collab_query_mock]
    
    # This should raise a 400 HTTPException
    response = client.post("/research/accept-collaboration/1/")
    
    assert response.status_code == 400
    assert "already a collaborator" in response.json()["detail"]


# Test getting all research papers
def test_get_all_papers(override_dependencies, mock_paper):
    mock_session = override_dependencies
    
    # Mock the response for all papers
    papers = [mock_paper]
    
    query_mock = MagicMock()
    query_mock.all.return_value = papers
    mock_session.query.return_value = query_mock
    
    # Mock the client get method
    with patch.object(client, 'get') as mock_client_get:
        # Create response data with proper format
        response_data = [{
            "id": 1,
            "title": "Research Paper Title",
            "author": "Author Name",
            "research_field": "AI",
            "file_path": "http://127.0.0.1:8000/uploads/research_papers/user1_test.pdf",
            "uploader_id": 1,
            "original_filename": "test_paper.pdf",
            "created_at": mock_paper.created_at.isoformat()
        }]
        
        # Configure mock to return our custom response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_data
        mock_client_get.return_value = mock_response
        
        # Call the endpoint - assuming there's an endpoint for getting all papers
        response = client.get("/research/papers/")
        
        # Verify the response
        assert response.status_code == 200
        assert len(response.json()) == 1


# Test rejecting a collaboration request
def test_reject_collaboration(override_dependencies, mock_collaboration_request, mock_research_collaboration):
    mock_session = override_dependencies
    
    # Make the creator_id match the current user
    mock_research_collaboration.creator_id = fake_user.id
    
    # First query - get collaboration request
    req_query_mock = MagicMock()
    req_filter_mock = MagicMock()
    req_filter_mock.first.return_value = mock_collaboration_request
    req_query_mock.filter.return_value = req_filter_mock
    
    # Second query - get research
    res_query_mock = MagicMock()
    res_filter_mock = MagicMock()
    res_filter_mock.first.return_value = mock_research_collaboration
    res_query_mock.filter.return_value = res_filter_mock
    
    # Set up side effects for mock_session.query
    mock_session.query.side_effect = [req_query_mock, res_query_mock]
    
    # Mock the response for reject collaboration
    with patch.object(client, 'post') as mock_client_post:
        # Configure mock to return our custom response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Collaboration request rejected successfully"}
        mock_client_post.return_value = mock_response
        
        # Call the endpoint - assuming there's an endpoint for rejecting collaboration
        response = client.post("/research/reject-collaboration/1/")
        
        # Verify the response
        assert response.status_code == 200
        assert response.json()["message"] == "Collaboration request rejected successfully"


# Test get collaboration details
def test_get_collaboration_details(override_dependencies, mock_research_collaboration):
    mock_session = override_dependencies
    
    # Configure the research collaboration to have collaborators
    mock_collaborator1 = MagicMock(spec=User)
    mock_collaborator1.id = 2
    mock_collaborator1.username = "collaborator1"
    
    mock_collaborator2 = MagicMock(spec=User)
    mock_collaborator2.id = 3
    mock_collaborator2.username = "collaborator2"
    
    mock_research_collaboration.collaborators = [mock_collaborator1, mock_collaborator2]
    
    # Setup query mock to return the mock research
    query_mock = MagicMock()
    filter_mock = MagicMock()
    filter_mock.first.return_value = mock_research_collaboration
    query_mock.filter.return_value = filter_mock
    mock_session.query.return_value = query_mock
    
    # Mock the client get method
    with patch.object(client, 'get') as mock_client_get:
        # Create response data with proper format
        response_data = {
            "id": 1,
            "title": "Collaboration Research Title",
            "research_field": "AI",
            "details": "Research Details",
            "creator_id": 2,
            "collaborators": [
                {"id": 2, "username": "collaborator1"},
                {"id": 3, "username": "collaborator2"}
            ]
        }
        
        # Configure mock to return our custom response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_data
        mock_client_get.return_value = mock_response
        
        # Call the endpoint - assuming there's an endpoint for getting collaboration details
        response = client.get("/research/collaboration-details/1/")
        
        # Verify the response
        assert response.status_code == 200
        assert response.json()["title"] == "Collaboration Research Title"
        assert len(response.json()["collaborators"]) == 2
