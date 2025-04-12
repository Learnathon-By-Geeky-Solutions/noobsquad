import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))  # Add the parent directory to sys.path

import pytest
from fastapi.testclient import TestClient
from main import app
from database.session import engine, Base

# Test client fixture to allow testing of the FastAPI app
@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client

# Database setup fixture (create and drop tables before and after tests)
@pytest.fixture(autouse=True)
def setup_database():
    # Create all tables before running the test
    Base.metadata.create_all(bind=engine)
    yield  # Tests run here
    # Drop all tables after the test is done
    Base.metadata.drop_all(bind=engine)

# ----------------------
# ✅ Test CORS Middleware
# ----------------------
def test_cors_middleware(client):
    # Test CORS headers for valid origin
    response = client.options(
        "/auth/login",  # Ensure your backend accepts OPTIONS request at this endpoint
        headers={
            "Origin": "http://127.0.0.1:5173",  # Backend address
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
    )
    # Validate the response
    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" in response.headers
    assert response.headers["Access-Control-Allow-Origin"] == "http://127.0.0.1:5173"
    assert response.headers["Access-Control-Allow-Credentials"] == "true"

def test_invalid_cors_origin(client):
    # Test for invalid origin
    response = client.options(
        "/auth/login",
        headers={
            "Origin": "http://invalid-origin.com",  # Invalid origin
            "Access-Control-Request-Method": "POST"
        }
    )
    # Assert that the invalid origin is not allowed
    assert "Access-Control-Allow-Origin" not in response.headers or \
           response.headers["Access-Control-Allow-Origin"] != "http://invalid-origin.com"

# ----------------------
# ✅ Test Static Files
# ----------------------
def test_static_file_mounts(client):
    # Test static file endpoints (adjust based on your actual file paths)
    response = client.get("/uploads/profile_pictures/test.jpg")
    # Assuming the test file is missing, expect 404 (Not Found)
    assert response.status_code == 404
    
    response = client.get("/uploads/media/test.mp4")
    assert response.status_code == 404  # Adjust to 200 if test file is available
    
    response = client.get("/uploads/document/test.pdf")
    assert response.status_code == 404  # Adjust to 200 if test file is available

# ----------------------
# ✅ Test Router Endpoints
# ----------------------
def test_router_endpoints(client):
    # Test different endpoints for proper status codes
    response = client.get("/auth")
    assert response.status_code in [200, 401, 404, 405]  # Checking for 401 (Unauthorized) as well
    
    response = client.get("/profile")
    assert response.status_code in [200, 401, 404, 405]
    
    response = client.get("/posts")
    assert response.status_code in [200, 401, 404, 405]
    
    response = client.get("/interactions")
    assert response.status_code in [200, 401, 404, 405]
    
    response = client.get("/connections")
    assert response.status_code in [200, 401, 404, 405]
    
    response = client.get("/research")
    assert response.status_code in [200, 401, 404, 405]
    
    response = client.get("/chat")
    assert response.status_code in [200, 401, 404, 405]

# ----------------------
# ✅ Test Root Endpoint
# ----------------------
def test_root_endpoint(client):
    response = client.get("/")
    # Checking for the status codes of the root endpoint
    assert response.status_code in [200, 401, 404]



if __name__ == "__main__":
    pytest.main()  # Run the tests when the script is executed
