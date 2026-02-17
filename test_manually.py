from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app, Base, get_db

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
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

app.dependency_overrides[get_db] = override_get_db

# Create a test client
client = TestClient(app)

def test_create_link():
    """Test creating a new short link."""
    response = client.post(
        "/links",
        json={"original_url": "https://www.fiverr.com/testuser/test-gig"}
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["original_url"] == "https://www.fiverr.com/testuser/test-gig"
    assert "short_code" in data
    assert len(data["short_code"]) == 6  # Default length is 6

    print("✅ test_create_link passed")

def test_invalid_url():
    """Test creating a link with invalid URL."""
    # Test non-Fiverr URL
    response = client.post(
        "/links",
        json={"original_url": "https://www.example.com/not-fiverr"}
    )
    assert response.status_code == 422  # Validation error

    print("✅ test_invalid_url passed")

def test_redirect():
    """Test redirect functionality."""
    # Create a link first
    original_url = "https://www.fiverr.com/testuser/redirect-test"
    response = client.post("/links", json={"original_url": original_url})
    short_code = response.json()["short_code"]

    # Test redirection
    response = client.get(f"/{short_code}", follow_redirects=False)
    assert response.status_code == 307  # Temporary redirect
    assert response.headers["location"] == original_url

    print("✅ test_redirect passed")

def test_stats_endpoint():
    """Test stats endpoint."""
    response = client.get("/stats")
    assert response.status_code == 200

    print("✅ test_stats_endpoint passed")

if __name__ == "__main__":
    # Drop tables for clean test run
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    print("Running manual tests...")
    test_create_link()
    test_invalid_url()
    test_redirect()
    test_stats_endpoint()
    print("All tests passed!")