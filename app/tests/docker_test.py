"""
Test script for Docker environment.

Usage:
    docker exec -it interview_api python tests/docker_test.py

This script tests the core functionality of the URL shortener API.
"""
import unittest
import requests
import time
from datetime import datetime

# Test against the API
# When running inside Docker container, we need to use localhost or 127.0.0.1
# The app is running on the same container, so localhost points to the app
API_URL = "http://127.0.0.1:8000"

class TestURLShortenerAPI(unittest.TestCase):
    """Test the URL shortener API in Docker."""

    def test_api_flow(self):
        """Test the entire API flow: create link, redirect, and get stats."""
        # 1. Create a link
        print("Testing link creation...")
        original_url = "https://www.fiverr.com/test/docker-test"
        response = requests.post(
            f"{API_URL}/links",
            json={"original_url": original_url}
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["original_url"], original_url)
        self.assertIn("short_code", data)
        short_code = data["short_code"]
        print(f"✅ Link created with short code: {short_code}")

        # 2. Test duplicate link creation
        print("Testing duplicate link creation...")
        response2 = requests.post(
            f"{API_URL}/links",
            json={"original_url": original_url}
        )
        self.assertEqual(response2.status_code, 201)
        data2 = response2.json()
        self.assertEqual(data2["short_code"], short_code)
        print("✅ Duplicate link returns existing short code")

        # 3. Test invalid URL
        print("Testing invalid URL...")
        response = requests.post(
            f"{API_URL}/links",
            json={"original_url": "https://www.example.com/not-fiverr"}
        )
        self.assertEqual(response.status_code, 422)
        print("✅ Invalid URL rejected")

        # 4. Test redirection
        print("Testing redirection...")
        response = requests.get(
            f"{API_URL}/{short_code}",
            allow_redirects=False
        )
        self.assertEqual(response.status_code, 307)
        self.assertEqual(response.headers["location"], original_url)
        print("✅ Redirection works")

        # 5. Wait a bit for the click to be registered
        print("Waiting for click to be processed...")
        time.sleep(1)

        # 6. Test stats
        print("Testing stats endpoint...")
        response = requests.get(f"{API_URL}/stats")
        self.assertEqual(response.status_code, 200)
        stats = response.json()
        self.assertTrue(len(stats) > 0)

        # Find our link in stats
        link_stats = next((s for s in stats if s["url"] == original_url), None)
        self.assertIsNotNone(link_stats)
        # Using proper assertGreaterEqual method as suggested by linter
        self.assertGreaterEqual(link_stats["total_clicks"], 1)
        print("✅ Stats endpoint works")

        # Print detailed stats
        print("\nLink statistics:")
        print(f"URL: {link_stats['url']}")
        print(f"Total clicks: {link_stats['total_clicks']}")
        print(f"Total earnings: ${link_stats['total_earnings']:.2f}")
        print("Monthly breakdown:")
        for month in link_stats["monthly_breakdown"]:
            print(f"  {month['month']}: ${month['earnings']:.2f}")

if __name__ == "__main__":
    print("Running Docker integration tests...")
    unittest.main()