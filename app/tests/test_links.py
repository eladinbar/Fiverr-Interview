import sys
import os
import pytest

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import Link

def test_create_link(client):
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


def test_create_duplicate_link(client):
    """Test that creating the same link twice returns the existing link."""
    url = "https://www.fiverr.com/testuser/another-test-gig"

    # Create the first link
    response1 = client.post("/links", json={"original_url": url})
    assert response1.status_code == 201
    data1 = response1.json()

    # Try to create the same link again
    response2 = client.post("/links", json={"original_url": url})
    assert response2.status_code == 201  # Should still return 201
    data2 = response2.json()

    # Both responses should have the same short_code
    assert data1["short_code"] == data2["short_code"]
    assert data1["id"] == data2["id"]


def test_create_invalid_link(client):
    """Test creating a link with invalid URL."""
    # Test non-Fiverr URL
    response = client.post(
        "/links",
        json={"original_url": "https://www.example.com/not-fiverr"}
    )
    assert response.status_code == 422  # Validation error

    # Test empty URL
    response = client.post("/links", json={"original_url": ""})
    assert response.status_code == 422

    # Test too long URL
    response = client.post(
        "/links",
        json={"original_url": "https://www.fiverr.com/" + "x" * 2050}
    )
    assert response.status_code == 422


def test_redirect_to_target(client):
    """Test that short links redirect to the original URL."""
    # Create a link first
    original_url = "https://www.fiverr.com/testuser/redirect-test"
    response = client.post("/links", json={"original_url": original_url})
    short_code = response.json()["short_code"]

    # Test redirection
    response = client.get(f"/{short_code}", follow_redirects=False)
    assert response.status_code == 307  # Temporary redirect
    assert response.headers["location"] == original_url


def test_redirect_nonexistent_link(client):
    """Test accessing a non-existent short link."""
    response = client.get("/nonexistent", follow_redirects=False)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_stats_pagination(test_db, client):
    """Test stats pagination."""
    db = test_db

    # Create multiple links
    urls = [f"https://www.fiverr.com/test/gig{i}" for i in range(15)]
    for url in urls:
        link = Link(original_url=url, short_code=f"test{urls.index(url):02d}")
        db.add(link)

    db.commit()

    # Test first page (default 10 per page)
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10

    # Test second page
    response = client.get("/stats?page=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5  # Only 5 left for page 2

    # Test with custom limit
    response = client.get("/stats?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5