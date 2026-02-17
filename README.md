# Fiverr URL Shortener Service

A URL shortening service for Fiverr sellers to generate short, clean, trackable URLs for their gigs, portfolios, or promotional destinations.

## Setup

### Prerequisites
- Docker and Docker Compose
- Git

### Installation and Running
1. Clone the repository:
   ```bash
   git clone https://github.com/eladinbar/Fiverr-Interview.git
   ```

2. Start the Docker containers:
   ```bash
   docker-compose up -d
   ```

3. The API will be available at:
   ```
   http://localhost:8000
   ```

4. To shut down:
   ```bash
   docker-compose down
   ```

## Architecture

### Core Features
1. **URL Shortening**: Generate unique short codes for Fiverr URLs
2. **Click Tracking**: Track clicks on shortened URLs
3. **Fraud Validation**: Validate clicks and award credits for valid clicks
4. **Analytics**: View statistics on clicks and earnings

### System Overview
The URL Shortener service is built with FastAPI, SQLAlchemy, and PostgreSQL. It follows a simple, modular architecture:

```
app/
├── main.py               # Main FastAPI application with endpoints and models
├── requirements.txt      # Python dependencies
├── tests/                # Test suite
```

### Component Interactions
- **FastAPI Application**: Handles HTTP requests and responses
- **Database Models**: SQLAlchemy models for Links and Clicks
- **Pydantic Schemas**: Data validation models
- **Fraud Validation**: Simulated validation logic for clicks

### Database Schema
1. **Links Table**:
   - `id`: Primary key
   - `original_url`: The target URL on Fiverr
   - `short_code`: Unique code for the shortened URL
   - `created_at`: Timestamp when the link was created

2. **Clicks Table**:
   - `id`: Primary key
   - `link_id`: Foreign key to Links table
   - `clicked_at`: Timestamp of the click
   - `is_valid`: Boolean indicating if the click passed fraud validation
   - `earnings`: Float value (0.05 if valid click, 0 if not)

### Data Flow
1. User submits a URL to be shortened
2. System checks for duplicates, generates a unique code if none found
3. When a shortened URL is accessed:
   - User is redirected to the original URL
   - Click is recorded with fraud validation (simulated)
   - If valid, credit is awarded
4. Analytics endpoint aggregates statistics on links and clicks

## API Endpoints

### 1. POST /links

Creates a new short link or returns an existing one.

**Request:**
```json
{
    "original_url": "https://www.fiverr.com/johndoe/create-stunning-logo-design"
}
```

**Response:**
```json
{
    "id": 1,
    "original_url": "https://www.fiverr.com/johndoe/create-stunning-logo-design",
    "short_code": "aB3cDe",
    "created_at": "2026-02-17T12:34:56"
}
```

### 2. GET /{short_code}

Redirects to the original URL and tracks the click. Awards 0.05$ credits for valid clicks.

### 3. GET /stats

Returns analytics for all generated links.

**Query Parameters:**
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 10, max: 100)

**Response:**
```json
[
    {
        "url": "https://www.fiverr.com/johndoe/create-stunning-logo-design",
        "total_clicks": 16,
        "total_earnings": 0.75,
        "monthly_breakdown": [
            { "month": "01/2026", "earnings": 0.50 },
            { "month": "02/2026", "earnings": 0.25 }
        ]
    }
]
```

## Testing

### Running Tests
Inside the Docker container:
```bash
# Run all tests
docker exec -it interview_api python tests/run_all_tests.py

# Run Docker integration tests only
docker exec -it interview_api python tests/docker_test.py

# Run specific test file
docker exec -it interview_api python -m pytest tests/test_links.py -v
```

### Testing Strategy
- **Unit Tests**: Test individual components like models and validators
- **Integration Tests**: Test API endpoints and database interactions
- **Edge Cases**: Tests for error conditions and boundary scenarios

### Edge Cases Handled
- **URL Validation**: Ensures URLs are properly formatted and from the Fiverr domain
- **Duplicate URLs**: Returns existing short codes for duplicate URLs
- **Short Code Collision**: Handles the unlikely case of short code collision
- **Pagination**: Efficiently handles large numbers of links
- **Error Handling**: Comprehensive error handling for all endpoints
- **Fraud Validation**: Simulates fraud validation with 500ms delay and 50% success rate

## AI Environment Setup

### Development Environment
- **IDE**: VS Code with Python extensions
- **AI Assistant**: Claude by Anthropic via Claude Code

### Plugins and Extensions
- FastAPI extension for API development
- Docker extension for container management
- Python Test Explorer for test execution
- SQLAlchemy support in IDE

### Code Rules
- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Handle errors gracefully with proper HTTP status codes
- Write thorough tests for core functionality
- Document complex logic with comments