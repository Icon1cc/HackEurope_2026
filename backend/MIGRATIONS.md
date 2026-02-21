# Database Migrations Guide

This project uses **Alembic** for managing database schema changes.

## Installation

Alembic is included in `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Workflow

### 1. Create a New Model

Define your model in `app/models/`:

```python
# app/models/user.py
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

Import it in `app/models/__init__.py`:

```python
from app.models.user import User

__all__ = ["User"]
```

### 2. Generate a Migration

Create an auto-generated migration:

```bash
alembic revision --autogenerate -m "Add users table"
```

This creates a migration file in `alembic/versions/` with detected schema changes.

**Review the generated migration** before applying it to ensure it's correct.

### 3. Apply Migrations

Apply all pending migrations:

```bash
alembic upgrade head
```

Upgrade to a specific migration:

```bash
alembic upgrade <revision_id>
```

### 4. Rollback Migrations

Downgrade to the previous migration:

```bash
alembic downgrade -1
```

Downgrade to a specific revision:

```bash
alembic downgrade <revision_id>
```

Downgrade all migrations:

```bash
alembic downgrade base
```

## Common Commands

```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Create an empty migration (manual edit)
alembic revision -m "Description"

# Check if there are pending migrations
alembic heads
```

## Docker Integration

Migrations are run automatically when the container starts:

```bash
# In docker-compose.yaml, the backend service runs:
docker-compose up -d

# To manually run migrations:
docker-compose exec backend alembic upgrade head

# To rollback:
docker-compose exec backend alembic downgrade -1
```

## Best Practices

1. **Always review auto-generated migrations** - They may not catch everything
2. **Test migrations locally first** - Run them on your local database before committing
3. **Keep migrations small** - One logical change per migration
4. **Never edit applied migrations** - Create a new migration instead
5. **Commit migrations with code** - Always commit migration files with model changes
6. **Test rollbacks** - Verify your downgrade() function works

## Example Migration

Auto-generated migration files look like:

```python
"""Add users table

Revision ID: 001abc
Revises:
Create Date: 2024-01-15 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '001abc'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
```

## Troubleshooting

### "No changes detected"

- Ensure models are imported in `app/models/__init__.py`
- Check that `target_metadata` in `alembic/env.py` references `Base` correctly
- Verify your model class extends `Base`

### "Can't locate revision identified by"

- Migration file may be deleted or corrupted
- Check `alembic/versions/` for the revision ID
- Verify database alembic_version table matches your migration state

### Connection errors in Docker

```bash
# Ensure database is healthy
docker-compose ps

# Check backend logs
docker-compose logs backend

# Manually run migrations with full output
docker-compose exec backend alembic upgrade head -v
```
