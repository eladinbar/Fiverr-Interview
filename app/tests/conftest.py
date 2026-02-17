import sys
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app, Base, get_db

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_main.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the tables
Base.metadata.create_all(bind=engine)


# Override the get_db dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the dependency for tests
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    """Create a test client for the app."""
    return TestClient(app)


@pytest.fixture
def test_db():
    """Setup a clean database before tests."""
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    # Create tables again
    Base.metadata.create_all(bind=engine)

    # Return a session
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()