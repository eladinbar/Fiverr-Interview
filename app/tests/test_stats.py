import sys
import os
import pytest
from datetime import datetime

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import Link, Click


def test_stats_with_clicks(test_db, client):
    """Test stats endpoint with clicks data."""
    db = test_db

    # Create a link
    link = Link(original_url="https://www.fiverr.com/test/stats", short_code="stats1")
    db.add(link)
    db.commit()
    db.refresh(link)

    # Add some clicks for different months
    # January clicks
    jan_clicks = [
        Click(link_id=link.id, is_valid=True, earnings=0.05, clicked_at=datetime(2026, 1, 1)),
        Click(link_id=link.id, is_valid=True, earnings=0.05, clicked_at=datetime(2026, 1, 15)),
        Click(link_id=link.id, is_valid=False, earnings=0.0, clicked_at=datetime(2026, 1, 20))
    ]

    # February clicks
    feb_clicks = [
        Click(link_id=link.id, is_valid=True, earnings=0.05, clicked_at=datetime(2026, 2, 5)),
        Click(link_id=link.id, is_valid=True, earnings=0.05, clicked_at=datetime(2026, 2, 10))
    ]

    for click in jan_clicks + feb_clicks:
        db.add(click)
    db.commit()

    # Test stats endpoint
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1  # Only one link
    link_stats = data[0]

    assert link_stats["url"] == "https://www.fiverr.com/test/stats"
    assert link_stats["total_clicks"] == 5  # 3 from Jan + 2 from Feb
    assert pytest.approx(link_stats["total_earnings"], abs=0.001) == 0.20  # 4 valid clicks * 0.05

    # Check monthly breakdown
    assert len(link_stats["monthly_breakdown"]) == 2  # Two months

    # Find January stats
    jan_stats = next((m for m in link_stats["monthly_breakdown"] if m["month"] == "01/2026"), None)
    assert jan_stats is not None
    assert pytest.approx(jan_stats["earnings"], abs=0.001) == 0.10  # 2 valid clicks in Jan

    # Find February stats
    feb_stats = next((m for m in link_stats["monthly_breakdown"] if m["month"] == "02/2026"), None)
    assert feb_stats is not None
    assert pytest.approx(feb_stats["earnings"], abs=0.001) == 0.10  # 2 valid clicks in Feb


def test_stats_empty_data(client):
    """Test stats endpoint with no data."""
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0  # No links


def test_stats_invalid_pagination(client):
    """Test stats endpoint with invalid pagination params."""
    # Test negative page number
    response = client.get("/stats?page=0")
    assert response.status_code == 422  # Validation error

    # Test negative limit
    response = client.get("/stats?limit=0")
    assert response.status_code == 422

    # Test too large limit
    response = client.get("/stats?limit=200")
    assert response.status_code == 422


def test_stats_page_out_of_bounds(test_db, client):
    """Test stats endpoint with out-of-bounds page number."""
    db = test_db

    # Create a link
    link = Link(original_url="https://www.fiverr.com/test/pagination", short_code="page1")
    db.add(link)
    db.commit()

    # Request a page that is beyond the data
    response = client.get("/stats?page=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0  # Empty result, not an error