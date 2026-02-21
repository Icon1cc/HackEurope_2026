# Backend Setup Guide

## Prerequisites
- Python 3.10+
- PostgreSQL 13+

## 1. PostgreSQL Setup

### Using Homebrew (macOS)
```bash
brew install postgresql
brew services start postgresql
```

### Using Docker
```bash
docker run --name hackeurope-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=hackeurope \
  -p 5432:5432 \
  -d postgres:latest
```

### Create Database Manually
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE hackeurope;

# Verify
\l
```

## 2. Virtual Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows
```

## 3. Install Dependencies


```bash
pip install -r requirements.txt
```

## 4. Environment Configuration

The `.env` file has been created with default settings:
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/hackeurope
```

Update if your PostgreSQL credentials differ.

## 5. Run the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

API Docs: `http://localhost:8000/docs` (Swagger UI)
ReDoc: `http://localhost:8000/redoc`

## 6. Creating Models

Example in `app/models/__init__.py`:

```python
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
```

## Docker Setup

### Using Docker Compose

```bash
# Start all services (PostgreSQL + Backend)
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Reset database
docker-compose down -v
docker-compose up -d
```

### Build Backend Image Only

```bash
docker build -t hackeurope-backend:latest ./backend
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/hackeurope \
  hackeurope-backend:latest
```

## Troubleshooting

### Connection Error: "could not connect to server"
- Ensure PostgreSQL is running
- Check DATABASE_URL in `.env`
- Verify PostgreSQL is listening on port 5432
- For Docker: ensure `depends_on` condition is met

### "password authentication failed"
- Check PostgreSQL username and password
- Reset PostgreSQL password: `psql -U postgres` then `\password postgres`
- In Docker: verify environment variables match

### AsyncIO Event Loop Error
- Make sure you're using Python 3.10+
- Restart the development server

### Docker Build Failures
- Clear Docker cache: `docker system prune -a`
- Rebuild: `docker-compose build --no-cache`
- Check disk space: `docker system df`
