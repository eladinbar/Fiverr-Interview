import sys
import os
import pytest
import asyncio
from unittest.mock import patch

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import Link, Click, validate_click


def test_validate_click():
    """Test the validate_click function returns True or False."""
    # Run multiple times to ensure we get both True and False results
    results = []
    for _ in range(100):
        result = asyncio.run(validate_click())
        results.append(result)

    # Check that we got at least one True and one False
    assert True in results
    assert False in results


@patch('app.main.validate_click')  # Update path for when main is imported via app module
def test_redirect_with_valid_click(mock_validate, test_db, client):
    """Test redirect with a valid click."""
    db = test_db

    # Create a link
    link = Link(original_url="https://www.fiverr.com/test/valid-click", short_code="valid")
    db.add(link)
    db.commit()

    # Mock the validate_click function to always return True
    mock_validate.return_value = True

    # Test the redirect
    response = client.get("/valid", follow_redirects=False)
    assert response.status_code == 307

    # Check that a click was recorded
    click = db.query(Click).filter(Click.link_id == link.id).first()
    assert click is not None
    assert click.is_valid is True
    assert pytest.approx(click.earnings, abs=0.001) == 0.05


@patch('app.main.validate_click')  # Update path for when main is imported via app module
def test_redirect_with_invalid_click(mock_validate, test_db, client):
    """Test redirect with an invalid click."""
    db = test_db

    # Create a link
    link = Link(original_url="https://www.fiverr.com/test/invalid-click", short_code="invalid")
    db.add(link)
    db.commit()

    # Mock the validate_click function to always return False
    mock_validate.return_value = False

    # Test the redirect
    response = client.get("/invalid", follow_redirects=False)
    assert response.status_code == 307

    # Check that a click was recorded
    click = db.query(Click).filter(Click.link_id == link.id).first()
    assert click is not None
    assert click.is_valid is False
    assert pytest.approx(click.earnings, abs=0.001) == 0.0


def test_very_long_short_code(client):
    """Test accessing a short code that is too long."""
    # Generate a very long short code (exceeding our reasonable limit)
    long_code = "a" * 50

    response = client.get(f"/{long_code}")
    assert response.status_code == 400
    assert "invalid short code" in response.json()["detail"].lower()


@patch('sqlalchemy.orm.Session.commit')
def test_database_error_handling(mock_commit, test_db, client):
    """Test handling database errors during redirect."""
    db = test_db

    # Create a link
    link = Link(original_url="https://www.fiverr.com/test/db-error", short_code="dberr")
    db.add(link)
    db.commit()

    # Mock the database commit to fail
    mock_commit.side_effect = Exception("Database error")

    # The redirect should still work even if tracking fails
    response = client.get("/dberr", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "https://www.fiverr.com/test/db-error"