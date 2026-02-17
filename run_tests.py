import os
import sys
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set environment variable for SQLite database
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

# Import our app models after setting the environment variable
from app.main import app, Base, Link, Click, generate_short_code

# Create test database
engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class TestLinkModel(unittest.TestCase):
    def setUp(self):
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        # Create tables again
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()

    def tearDown(self):
        self.db.close()

    def test_create_link(self):
        """Test creating a link."""
        link = Link(original_url="https://www.fiverr.com/test/link", short_code="testcode")
        self.db.add(link)
        self.db.commit()

        # Retrieve the link
        retrieved_link = self.db.query(Link).filter(Link.short_code == "testcode").first()
        self.assertEqual(retrieved_link.original_url, "https://www.fiverr.com/test/link")
        self.assertEqual(retrieved_link.short_code, "testcode")

    def test_click_model(self):
        """Test creating clicks for a link."""
        # Create a link first
        link = Link(original_url="https://www.fiverr.com/test/click", short_code="clicktest")
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)

        # Add some clicks
        click1 = Click(link_id=link.id, is_valid=True, earnings=0.05)
        click2 = Click(link_id=link.id, is_valid=False, earnings=0.0)
        self.db.add(click1)
        self.db.add(click2)
        self.db.commit()

        # Retrieve the clicks
        clicks = self.db.query(Click).filter(Click.link_id == link.id).all()
        self.assertEqual(len(clicks), 2)
        self.assertAlmostEqual(sum(click.earnings for click in clicks), 0.05)

    def test_short_code_generation(self):
        """Test short code generation."""
        code = generate_short_code()
        self.assertEqual(len(code), 6)

        # Test with custom length
        code = generate_short_code(length=8)
        self.assertEqual(len(code), 8)

if __name__ == "__main__":
    print("Running tests...")
    unittest.main()