import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from database.session import engine, Base, SessionLocal
from main import app

# Import all models to register with Base
from models.user import User
from models.connection import Connection
from models.chat import Chat  # Verify this matches your chat.py
from models.post import Post
from models.notifications import Notification
# Add other models from your coverage report if missing
from models.research_paper import ResearchPaper
from models.collaboration_request import CollaborationRequest
from models.research_collaboration import ResearchCollaboration

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # Create all tables before tests start
    Base.metadata.drop_all(bind=engine)  # Ensure clean state
    Base.metadata.create_all(bind=engine)
    yield
    # Drop all tables after tests finish
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()  # Roll back any uncommitted changes
        db.close()

@pytest.fixture
def client():
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.rollback()
            db.close()
    app.dependency_overrides[Session] = override_get_db
    return TestClient(app)