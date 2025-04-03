import pytest
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

from database.session import engine, Base

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # Create all tables before any tests run
    Base.metadata.create_all(bind=engine)
    yield
    # Drop all tables after all tests finish
    Base.metadata.drop_all(bind=engine)