import os
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import asyncio
from unittest.mock import patch

# Set environment variable for SQLite database
os.environ["DATABASE_URL"] = "sqlite:///./test_api.db"

# Import our app modules after setting the environment variable
from app.main import app, Base, Link, Click, get_db

# Create test database
engine = create_engine("sqlite:///./test_api.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# Override the get_db dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        # Clean database
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_create_link(self):
        """Test creating a new link via API."""
        response = client.post(
            "/links",
            json={"original_url": "https://www.fiverr.com/testuser/api-test"}
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["original_url"], "https://www.fiverr.com/testuser/api-test")
        self.assertIn("short_code", data)
        self.assertEqual(len(data["short_code"]), 6)

    def test_duplicate_link(self):
        """Test that creating the same link twice returns the existing link."""
        url = "https://www.fiverr.com/testuser/duplicate-test"

        # Create first link
        response1 = client.post("/links", json={"original_url": url})
        self.assertEqual(response1.status_code, 201)
        data1 = response1.json()

        # Create same link again
        response2 = client.post("/links", json={"original_url": url})
        self.assertEqual(response2.status_code, 201)
        data2 = response2.json()

        # Check they're the same
        self.assertEqual(data1["id"], data2["id"])
        self.assertEqual(data1["short_code"], data2["short_code"])

    def test_invalid_url(self):
        """Test validation for invalid URLs."""
        # Non-Fiverr URL
        response = client.post("/links", json={"original_url": "https://www.example.com"})
        self.assertEqual(response.status_code, 422)

        # Empty URL
        response = client.post("/links", json={"original_url": ""})
        self.assertEqual(response.status_code, 422)

        # Too long URL
        response = client.post("/links", json={"original_url": "https://www.fiverr.com/" + "x" * 2050})
        self.assertEqual(response.status_code, 422)

    @patch('app.main.validate_click')
    def test_redirect(self, mock_validate):
        """Test redirection works correctly."""
        # Mock the validate_click function to always return True
        async def mock_validate_click():
            return True

        mock_validate.return_value = mock_validate_click()

        # Create a link first
        original_url = "https://www.fiverr.com/testuser/redirect-test"
        response = client.post("/links", json={"original_url": original_url})
        self.assertEqual(response.status_code, 201)
        short_code = response.json()["short_code"]

        # Test redirection
        response = client.get(f"/{short_code}", allow_redirects=False)
        self.assertEqual(response.status_code, 307)
        self.assertEqual(response.headers["location"], original_url)

    def test_stats_pagination(self):
        """Test stats endpoint pagination."""
        # Create a bunch of links
        db = TestingSessionLocal()
        for i in range(15):
            link = Link(
                original_url=f"https://www.fiverr.com/test/gig{i}",
                short_code=f"test{i:02d}"
            )
            db.add(link)
        db.commit()
        db.close()

        # Test first page (default 10 per page)
        response = client.get("/stats")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 10)

        # Test second page
        response = client.get("/stats?page=2")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 5)

        # Test with custom limit
        response = client.get("/stats?limit=5")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 5)

if __name__ == "__main__":
    print("Running API endpoint tests...")
    unittest.main()