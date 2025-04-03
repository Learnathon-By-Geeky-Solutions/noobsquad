import pytest
from sqlalchemy.orm import Session
import sys
from pathlib import Path
from fastapi.testclient import TestClient
sys.path.append(str(Path(__file__).resolve().parents[1]))

from database.session import engine, Base, SessionLocal
from main import app
# Import all models to register them with Base
from models.user import User
from models.connection import Connection
from models.chat import Message
from models.post import Post
from models.notifications import Notification
# Add other models as needed

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # Create all tables before tests start
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
        db.close()

@pytest.fixture
def client():
    # Override the app's DB dependency
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[Session] = override_get_db
    return TestClient(app)