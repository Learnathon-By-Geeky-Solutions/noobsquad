# import sys
# from pathlib import Path
# import pytest
# from fastapi.testclient import TestClient
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from main import app
# from database.session import Base
# from core.dependencies import get_db
# from database.session import SessionLocal, Base, engine  
# from models.user import User
# from core.security import hash_password
# import os
# import shutil
# import secrets

# # Add backend directory to sys.path for imports
# sys.path.append(str(Path(__file__).resolve().parents[1]))


# Base.metadata.create_all(bind=engine)

# # Override dependency for testing
# def override_get_db():
#     try:
#         db = SessionLocal()
#         yield db
#     finally:
#         db.close()

# app.dependency_overrides[get_db] = override_get_db

# # Initialize FastAPI test client
# client = TestClient(app)

# # ----------------------
# # 🔧 Fixture for setup and teardown
# # ----------------------
# @pytest.fixture(autouse=True)
# def setup_and_teardown():
#     # Setup: Create tables and clear upload directory
#     Base.metadata.create_all(bind=engine)
#     upload_dir = "uploads/profile_pictures"
#     if os.path.exists(upload_dir):
#         shutil.rmtree(upload_dir)
#     os.makedirs(upload_dir, exist_ok=True)
    
#     yield
    
#     # Teardown: Drop tables and remove upload directory
#     Base.metadata.drop_all(bind=engine)
#     if os.path.exists(upload_dir):
#         shutil.rmtree(upload_dir)

# # ----------------------
# # 🔧 Fixture for test user
# # ----------------------
# @pytest.fixture
# def test_user():
#     db = SessionLocal()
#     user = db.query(User).filter(User.email == "test@example.com").first()
#     if not user:
#         user = User(
#             id=1,
#             username="testuser",
#             email="test@example.com",
#             hashed_password=hash_password("testpass"),
#             is_active=True
#         )
#         db.add(user)
#         db.commit()
#         db.refresh(user)
#     db.close()
#     return user

# # ----------------------
# # 🔧 Fixture for auth headers
# # ----------------------
# @pytest.fixture
# def auth_headers(test_user):
#     response = client.post(
#         "/auth/token",
#         data={
#             "username": "testuser",
#             "password": "testpass"
#         }
#     )
#     assert response.status_code == 200, "Failed to obtain token"
#     token = response.json()["access_token"]
#     return {"Authorization": f"Bearer {token}"}

# # ----------------------
# # ✅ Test complete_profile_step1 success
# # ----------------------
# def test_complete_profile_step1_success(auth_headers):
#     response = client.post(
#         "/profile/step1",
#         data={
#             "university_name": "Test University",
#             "department": "Computer Science",
#             "fields_of_interest": ["Artificial Intelligence", "Data Science"]
#         },
#         headers=auth_headers
#     )
    
#     assert response.status_code == 200
#     data = response.json()
#     assert data["university_name"] == "Test University"
#     assert data["department"] == "Computer Science"
#     assert data["fields_of_interest"] == ["Artificial Intelligence", "Data Science"]
#     assert data["profile_completed"] is True

# # ----------------------
# # ✅ Test complete_profile_step1 invalid fields
# # ----------------------
# def test_complete_profile_step1_invalid_fields(auth_headers):
#     response = client.post(
#         "/profile/step1",
#         data={
#             "university_name": "Test University",
#             "department": "Computer Science",
#             "fields_of_interest": ["Invalid Field"]
#         },
#         headers=auth_headers
#     )
    
#     # Note: Your endpoint doesn't validate fields_of_interest against RELEVANT_FIELDS.
#     # If validation is added, this test would expect a 400 status code.
#     assert response.status_code == 200  # Update if validation is implemented

# # ----------------------
# # ✅ Test complete_profile_step1 unauthorized
# # ----------------------
# def test_complete_profile_step1_unauthorized():
#     response = client.post(
#         "/profile/step1",
#         data={
#             "university_name": "Test University",
#             "department": "Computer Science",
#             "fields_of_interest": ["Artificial Intelligence"]
#         }
#     )
    
#     assert response.status_code == 401
#     assert response.json()["detail"] == "Not authenticated"


# # ----------------------
# # ✅ Test upload_profile_picture invalid file type
# # ----------------------
# def test_upload_profile_picture_invalid_file_type(auth_headers, tmp_path):
#     # Create a temporary non-image file
#     text_path = tmp_path / "test_file.txt"
#     with open(text_path, "w") as f:
#         f.write("This is not an image")
    
#     with open(text_path, "rb") as f:
#         response = client.post(
#             "/profile/upload_picture",
#             files={"file": ("test_file.txt", f, "text/plain")},
#             headers=auth_headers
#         )
    
#     assert response.status_code == 400
#     assert response.json()["detail"] == "Invalid file type. Allowed: jpg, jpeg, png, gif, webp."

