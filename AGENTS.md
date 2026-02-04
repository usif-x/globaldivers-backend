# AGENTS.md - Coding Guidelines for Top Divers Backend

## Build & Development Commands

```bash
# Setup
pip install -r requirements.txt
cp .env.example .env

# Development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
# Or using the CLI:
python main.py dev --reload

# Production server
python main.py prod --workers 4
# Or directly with gunicorn:
gunicorn -c gunicorn.conf.py main:app

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1

# Testing (when implemented)
pytest
pytest tests/test_specific.py::test_function -v
pytest -k "test_name_pattern"

# Linting/Formatting (install if needed)
ruff check app/
ruff format app/
```

## Architecture Overview

FastAPI + SQLAlchemy ORM + PostgreSQL with layered architecture:

- **Routes** (`app/routes/`): API endpoints using `APIRouter`, handle HTTP concerns
- **Services** (`app/services/`): Business logic, database operations via service classes (e.g., `TripServices`)
- **Models** (`app/models/`): SQLAlchemy ORM models with `Mapped[]` type annotations
- **Schemas** (`app/schemas/`): Pydantic models for request/response validation
- **Core** (`app/core/`): Config, database, security, dependencies, exception handlers

## Code Style Guidelines

### Imports (3 groups with blank lines)

```python
# 1. Standard library
from datetime import datetime
from typing import List, Optional

# 2. Third-party packages
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

# 3. Local application
from app.core.database import get_db
from app.models.trip import Trip
from app.schemas.trip import TripResponse
```

### Naming Conventions

- **Variables/Functions**: `snake_case` (e.g., `get_all_trips`, `user_id`)
- **Classes**: `PascalCase` (e.g., `TripServices`, `CreateTrip`)
- **Router instances**: Suffix with `_routes` (e.g., `trip_routes`, `auth_routes`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `JWT_SECRET_KEY`)
- **Private methods**: Prefix with `_` (e.g., `_convert_filenames_to_urls`)

### Type Annotations

- Use type hints everywhere
- SQLAlchemy 2.0 style: `Mapped[int]`, `Mapped[str]`, `Mapped[list[str]]`
- Pydantic models for API inputs/outputs
- Return type hints on all functions

### Error Handling

- Use `@db_exception_handler` decorator on service methods for DB operations
- Raise `HTTPException` with appropriate status codes in routes/services
- Use specific status codes: 400 (bad request), 404 (not found), 409 (conflict), 422 (validation)
- Log errors using `logging.getLogger(__name__)`

### Service Layer Pattern

```python
class TripServices:
    def __init__(self, db: Session):
        self.db = db

    @db_exception_handler
    async def create_trip(self, trip: CreateTrip) -> Trip:
        # Business logic here
        pass
```

### Route Pattern

```python
trip_routes = APIRouter(prefix="/trips", tags=["Trip Endpoints"])

@trip_routes.get("/", response_model=list[TripResponse])
@cache(expire=600)
async def get_all_trips(db: Session = Depends(get_db)):
    return TripServices(db).get_all_trips()
```

### Database Operations

- Use `select()` with SQLAlchemy 2.0 syntax: `db.execute(stmt).scalars().first()`
- Wrap blocking DB calls in `run_in_threadpool` for async endpoints
- Use relationships with `passive_deletes=True` for cascades

### Configuration

- All settings in `app/core/config.py` using Pydantic Settings
- Environment variables loaded from `.env` file
- Access via: `from app.core.config import settings`

### Security

- Use dependency injection: `get_current_user`, `get_current_admin`
- Rate limiting with `@limiter.limit("5/minute")` decorator
- Never commit secrets or .env files

## File Organization

- One model per file in `app/models/`
- One schema file per entity in `app/schemas/`
- One service class per entity in `app/services/`
- Register routes in `app/routes/all.py`

## Documentation

- Add docstrings to modules, classes, and complex functions
- Use triple double quotes for docstrings
- Keep lines under 100 characters when possible
- Add comments for complex business logic only
