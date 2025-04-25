import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1])) 
# Import your main app that includes the router
from main import app
from models.post import Event
from models.user import User
from api.v1.endpoints.auth import get_current_user
from core.dependencies import get_db

# Create test client
client = TestClient(app)

# Mock data
@pytest.fixture
def mock_events():
    now = datetime.utcnow()
    return [
        # Within 7 days events
        Event(id=1, post_id=101, user_id=1, title="Event 1", description="Description 1", 
              event_datetime=now + timedelta(days=2), location="Location 1", image_url="http://example.com/1.jpg"),
        Event(id=2, post_id=102, user_id=1, title="Event 2", description="Description 2", 
              event_datetime=now + timedelta(days=5), location="Location 2", image_url="http://example.com/2.jpg"),
        # Within 30 days events
        Event(id=3, post_id=103, user_id=1, title="Event 3", description="Description 3", 
              event_datetime=now + timedelta(days=10), location="Location 3", image_url="http://example.com/3.jpg"),
        Event(id=4, post_id=104, user_id=1, title="Event 4", description="Description 4", 
              event_datetime=now + timedelta(days=25), location="Location 4", image_url="http://example.com/4.jpg"),
        # Within year events
        Event(id=5, post_id=105, user_id=1, title="Event 5", description="Description 5", 
              event_datetime=now + timedelta(days=60), location="Location 5", image_url="http://example.com/5.jpg"),
        Event(id=6, post_id=106, user_id=1, title="Event 6", description="Description 6", 
              event_datetime=now + timedelta(days=300), location="Location 6", image_url="http://example.com/6.jpg"),
    ]

@pytest.fixture
def mock_current_user():
    return User(id=1, username="testuser", email="test@example.com")

# Test grouped events endpoint
def test_get_grouped_event_ids(mock_events):
    # Create a mock db that will respond to our specific query
    mock_db = MagicMock()
    
    # Set up mock query to return the appropriate data for each call
    # First call - events within 7 days
    query1 = MagicMock()
    query1.all.return_value = [Event(id=1), Event(id=2)]
    
    # Second call - events within 30 days
    query2 = MagicMock()
    query2.all.return_value = [Event(id=3), Event(id=4)]
    
    # Third call - events within year
    query3 = MagicMock()
    query3.all.return_value = [Event(id=5), Event(id=6)]
    
    # Configure the mock db to return the appropriate query for each filter
    mock_db.query.return_value.filter.side_effect = [query1, query2, query3]
    
    # Override dependencies for this test
    def override_get_db():
        return mock_db
        
    def override_get_current_user():
        return User(id=1, username="testuser", email="test@example.com")
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    try:
        # Make the request
        response = client.get("/top/events/grouped-by-time")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "within_7_days" in data
        assert "within_30_days" in data
        assert "within_year" in data
        assert len(data["within_7_days"]) == 2
        assert len(data["within_30_days"]) == 2
        assert len(data["within_year"]) == 2
        assert 1 in data["within_7_days"]
        assert 2 in data["within_7_days"]
        assert 3 in data["within_30_days"]
        assert 4 in data["within_30_days"]
        assert 5 in data["within_year"]
        assert 6 in data["within_year"]
    finally:
        # Clear the overrides after the test
        app.dependency_overrides.clear()

# Test paginated events by IDs endpoint
def test_get_paginated_events_by_ids(mock_events):
    # Create a mock DB session
    mock_db = MagicMock()
    
    # Setup mock for the specific query we need
    mock_db.query.return_value.filter.return_value.all.return_value = [
        mock_events[0], mock_events[1], mock_events[2], mock_events[3]
    ]
    
    # Override dependencies for this test
    def override_get_db():
        return mock_db
        
    def override_get_current_user():
        return User(id=1, username="testuser", email="test@example.com")
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    try:
        # Make the request with default limit (4)
        response = client.get("/top/events/by-ids/paginated", params={"event_ids": [1, 2, 3, 4]})
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4
        assert data[0]["id"] == 1
        assert data[1]["id"] == 2
        assert data[2]["id"] == 3
        assert data[3]["id"] == 4
        
        # Reset mock for next call
        mock_db.reset_mock()
        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_events[1], mock_events[2]
        ]
        
        # Test with custom offset and limit
        response = client.get("/top/events/by-ids/paginated", 
                             params={"event_ids": [1, 2, 3, 4], "offset": 1, "limit": 2})
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == 2
        assert data[1]["id"] == 3
    finally:
        # Clear the overrides after the test
        app.dependency_overrides.clear()

# Test empty results
def test_get_paginated_events_empty_results():
    # Create a mock DB session
    mock_db = MagicMock()
    
    # Setup mock for empty results
    mock_db.query.return_value.filter.return_value.all.return_value = []
    
    # Override dependencies for this test
    def override_get_db():
        return mock_db
        
    def override_get_current_user():
        return User(id=1, username="testuser", email="test@example.com")
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    try:
        # Make the request
        response = client.get("/top/events/by-ids/paginated", params={"event_ids": [999]})
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0
    finally:
        # Clear the overrides after the test
        app.dependency_overrides.clear()

# Test handling of Query parameter parsing
def test_event_ids_parsing(mock_events):
    # Create a mock DB session
    mock_db = MagicMock()
    
    # Setup mock database query
    mock_db.query.return_value.filter.return_value.all.return_value = [
        mock_events[0], mock_events[1]
    ]
    
    # Override dependencies for this test
    def override_get_db():
        return mock_db
        
    def override_get_current_user():
        return User(id=1, username="testuser", email="test@example.com")
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    try:
        # Test with multiple event_ids
        response = client.get("/top/events/by-ids/paginated", params={"event_ids": [1, 2]})
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    finally:
        # Clear the overrides after the test
        app.dependency_overrides.clear()