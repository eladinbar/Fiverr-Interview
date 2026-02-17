from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import Base, Link, Click

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_db():
    """Setup the database for testing."""
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    # Create tables again
    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal()

def test_link_model():
    """Test the Link model."""
    db = setup_db()

    # Create a new link
    link = Link(original_url="https://www.fiverr.com/test/link", short_code="testcode")
    db.add(link)
    db.commit()

    # Retrieve the link
    retrieved_link = db.query(Link).filter(Link.short_code == "testcode").first()

    # Check that it matches
    assert retrieved_link.original_url == "https://www.fiverr.com/test/link"
    assert retrieved_link.short_code == "testcode"

    print("✅ test_link_model passed")

def test_click_model():
    """Test the Click model."""
    db = setup_db()

    # Create a link first
    link = Link(original_url="https://www.fiverr.com/test/click", short_code="clicktest")
    db.add(link)
    db.commit()
    db.refresh(link)

    # Add some clicks
    click1 = Click(link_id=link.id, is_valid=True, earnings=0.05)
    click2 = Click(link_id=link.id, is_valid=False, earnings=0.0)
    db.add(click1)
    db.add(click2)
    db.commit()

    # Retrieve the clicks
    clicks = db.query(Click).filter(Click.link_id == link.id).all()

    # Check that they match
    assert len(clicks) == 2
    assert sum(click.earnings for click in clicks) == 0.05

    print("✅ test_click_model passed")

if __name__ == "__main__":
    print("Running database model tests...")
    test_link_model()
    test_click_model()
    print("All database tests passed!")