from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, validator
from sqlalchemy import create_engine, Column, Integer, String, TIMESTAMP, Boolean, Float, ForeignKey, func, extract
from sqlalchemy.orm import sessionmaker, declarative_base, Session, relationship
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from typing import List, Optional
import random
import string
import asyncio
import re
import os

# --- Database Setup ---
# NOTE: In Docker, the host is 'db' (service name).
# If running locally (outside Docker), change 'db' to 'localhost' and port to '5433'.
# For testing, we can override with a SQLite database
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://app:app@db:5432/app")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- DB Models ---
class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String, nullable=False, index=True)
    short_code = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationship with Click model
    clicks = relationship("Click", back_populates="link")

class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, index=True)
    link_id = Column(Integer, ForeignKey("links.id"), nullable=False)
    clicked_at = Column(TIMESTAMP, server_default=func.now())
    is_valid = Column(Boolean, nullable=False)
    earnings = Column(Float, nullable=False)

    # Relationship with Link model
    link = relationship("Link", back_populates="clicks")

# Create tables
Base.metadata.create_all(bind=engine)

# --- Pydantic Schemas ---
class LinkCreate(BaseModel):
    original_url: str

    @validator('original_url')
    def url_must_be_valid_fiverr(cls, v):
        # Check if URL is empty
        if not v or v.isspace():
            raise ValueError('URL cannot be empty')

        # Check if URL is too long (max 2048 chars is common browser limit)
        if len(v) > 2048:
            raise ValueError('URL is too long (max 2048 characters)')

        # Check if URL has fiverr.com domain
        if 'fiverr.com' not in v:
            raise ValueError('URL must be from fiverr.com domain')

        # Simple regex to validate URL format
        url_pattern = re.compile(
            r'^(https?://)?(www\.)?'  # http:// or https:// + www. (optional)
            r'([a-zA-Z0-9-]+\.)*fiverr\.com'  # domain
            r'(/[a-zA-Z0-9-._~:/?#[\]@!$&\'()*+,;=]*)?$'  # path
        )

        if not url_pattern.match(v):
            raise ValueError('Invalid URL format')

        return v

class LinkResponse(BaseModel):
    id: int
    original_url: str
    short_code: str
    created_at: datetime

    class Config:
        from_attributes = True

class MonthlyStats(BaseModel):
    month: str  # Format: "MM/YYYY"
    earnings: float

class LinkStats(BaseModel):
    url: str
    total_clicks: int
    total_earnings: float
    monthly_breakdown: List[MonthlyStats]

# --- Helper Functions ---
def generate_short_code(length=6):
    """Generate a random short code for URLs."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

async def validate_click():
    """Simulate fraud validation that takes 500ms and returns true/false with 50% probability."""
    await asyncio.sleep(0.5)  # Simulate 500ms processing
    return random.choice([True, False])  # 50% probability

# --- FastAPI App ---
app = FastAPI()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Fiverr URL Shortener API. Sanity Check Passed."}

# 1. POST /links - Short link generation
@app.post("/links", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
def create_short_link(link_in: LinkCreate, db: Session = Depends(get_db)):
    try:
        # Check if the URL already exists
        existing_link = db.query(Link).filter(Link.original_url == link_in.original_url).first()
        if existing_link:
            return existing_link

        # Generate a unique short code (limit attempts to avoid infinite loop)
        max_attempts = 10  # Reasonable number, collision is very unlikely
        attempts = 0

        while attempts < max_attempts:
            short_code = generate_short_code()
            # Check if short_code is already used
            if not db.query(Link).filter(Link.short_code == short_code).first():
                break
            attempts += 1

        # Very unlikely, but handle the case where we couldn't generate a unique code
        if attempts >= max_attempts:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not generate unique short code. Please try again."
            )

        # Create new link
        new_link = Link(original_url=link_in.original_url, short_code=short_code)
        db.add(new_link)
        db.commit()
        db.refresh(new_link)
        return new_link

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

# 2. GET /:short_code - Redirection and Tracking
@app.get("/{short_code}")
async def redirect_to_target(short_code: str, db: Session = Depends(get_db)):
    try:
        # Validate input
        if not short_code or len(short_code) > 20:  # Assuming reasonable limits
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid short code format"
            )

        # Find the link
        link = db.query(Link).filter(Link.short_code == short_code).first()
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Short link not found"
            )

        try:
            # Validate the click (async operation that takes 500ms)
            is_valid = await validate_click()

            # Record the click
            earnings = 0.05 if is_valid else 0.0
            new_click = Click(link_id=link.id, is_valid=is_valid, earnings=earnings)
            db.add(new_click)
            db.commit()

        except Exception as e:
            # If click tracking fails, log it but still redirect the user
            # In a real app, you might want to log this error
            db.rollback()
            print(f"Error tracking click: {str(e)}")

        # Redirect to the original URL
        return RedirectResponse(url=link.original_url)

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

# Helper functions for stats

def get_paginated_links(db: Session, page: int, limit: int):
    """Get paginated links with bounds checking."""
    offset = (page - 1) * limit
    total_links = db.query(func.count(Link.id)).scalar()

    # If page is out of bounds, return empty list
    if offset >= total_links and total_links > 0:
        return []

    return db.query(Link).offset(offset).limit(limit).all()

def get_link_total_stats(db: Session, link_id: int):
    """Get total clicks and earnings for a link."""
    total_clicks = db.query(func.count(Click.id)).filter(Click.link_id == link_id).scalar() or 0
    total_earnings = db.query(func.sum(Click.earnings)).filter(Click.link_id == link_id).scalar() or 0.0
    return total_clicks, float(total_earnings or 0.0)

def get_monthly_breakdown(db: Session, link_id: int):
    """Get monthly earnings breakdown for a link."""
    monthly_stats = db.query(
        extract('month', Click.clicked_at).label('month'),
        extract('year', Click.clicked_at).label('year'),
        func.sum(Click.earnings).label('earnings')
    ).filter(Click.link_id == link_id).group_by(
        extract('month', Click.clicked_at),
        extract('year', Click.clicked_at)
    ).order_by(
        extract('year', Click.clicked_at),
        extract('month', Click.clicked_at)
    ).all()

    result = []
    for stat in monthly_stats:
        if stat.month is not None and stat.year is not None:
            month_str = f"{int(stat.month):02d}/{int(stat.year)}"
            result.append(MonthlyStats(
                month=month_str,
                earnings=float(stat.earnings or 0.0)
            ))
    return result

# 3. GET /stats - Global analytics with pagination
@app.get("/stats", response_model=List[LinkStats])
def get_stats(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page")
):
    try:
        # Get paginated links
        links = get_paginated_links(db, page, limit)

        result = []
        for link in links:
            try:
                # Get total stats
                total_clicks, total_earnings = get_link_total_stats(db, link.id)

                # Get monthly breakdown
                monthly_breakdown = get_monthly_breakdown(db, link.id)

                # Build the response object
                result.append(LinkStats(
                    url=link.original_url,
                    total_clicks=total_clicks,
                    total_earnings=total_earnings,
                    monthly_breakdown=monthly_breakdown
                ))
            except Exception as e:
                # If processing a single link fails, continue with others
                print(f"Error processing stats for link {link.id}: {str(e)}")

        return result

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )