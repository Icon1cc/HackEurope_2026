# Backend Runbook

This README contains the exact commands used to run and debug the backend in this repo.

## Prerequisites

- Docker Desktop running
- Python `3.13.x` (for local backend runs)

## Important Paths

- Repo root: `<repo-root>`
- Backend env file (used by settings): `backend/.env`

## 1. Run Postgres Only (Docker)

```bash
cd <repo-root>
docker compose up -d postgres
docker compose ps postgres
docker compose logs -f postgres
```

Expected mapping:
- host machine -> `localhost:5433`
- inside Docker network -> `postgres:5432`

## 2. Run Backend + Postgres (Docker, Recommended)

```bash
cd <repo-root>
docker compose up -d --build backend
docker compose ps
docker compose logs -f backend
```

Health check:

```bash
curl -sS -i http://127.0.0.1:8000/health
```

API docs:
- `http://127.0.0.1:8000/docs`

## 3. Run Backend Locally (with Docker Postgres)

Start Postgres:

```bash
cd <repo-root>
docker compose up -d postgres
```

Set backend env (in `backend/.env`):

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/hackeurope
GEMINI_API_KEY=your_gemini_api_key
# Optional fallback (supported by backend): GCP_API_KEY=your_gemini_api_key
```

Then run backend locally:

```bash
cd <repo-root>/backend
uv sync
alembic upgrade head
uvicorn app.main:app --reload
```

If you are not using `uv`:

```bash
cd <repo-root>/backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## 4. Postgres Connection for DB Extensions

Use these values when the extension runs on your host machine:

- Host: `localhost`
- Port: `5433`
- Database: `hackeurope`
- Username: `postgres`
- Password: `postgres`

Connection URI:

```text
postgresql://postgres:postgres@localhost:5433/hackeurope
```

If the extension itself runs inside Docker on the same network:

- Host: `postgres`
- Port: `5432`
- Database: `hackeurope`
- Username: `postgres`
- Password: `postgres`

## 5. Connect to Postgres Without Installing `psql` Locally

If `psql` is not installed on your Mac, use the container client:

```bash
cd <repo-root>
docker compose exec postgres psql -U postgres -d hackeurope
```

## 6. Useful Debug Commands We Used

```bash
cd <repo-root>
docker compose ps
docker compose ps postgres
docker compose logs --tail=200 backend
docker compose logs -f postgres
```

## 7. API Endpoints

| Route group | Base path | Key endpoint |
|---|---|---|
| Health | `/health` | `GET /health` |
| Extraction | `/api/v1/extraction` | `POST /api/v1/extraction/` — upload invoice PDF/image, runs full 12-step pipeline (extract → signals → rubric → LLM analysis → route → persist) |
| Pricing | `/api/v1/pricing` | `POST /api/v1/pricing/sync` — sync cloud pricing from AWS/Azure/GCP APIs |
| Vendors | `/api/v1/vendors` | CRUD for vendor records |
| Invoices | `/api/v1/invoices` | CRUD + list invoices |
| Market data | `/api/v1/market-data` | Query aggregated market prices |

Full interactive docs: `http://localhost:8000/docs`

## 8. Common Errors and Fixes

- `connection to server at "127.0.0.1", port 5432 failed`:
  - Use port `5433` for host-machine connections.

- `zsh: command not found: psql`:
  - Use `docker compose exec postgres psql -U postgres -d hackeurope`.

- `TypeError ... ModelType | None`:
  - You are using old Python. Use Python `3.13`.

- `python-dotenv could not parse statement`:
  - Ensure headings in `backend/.env` are commented with `#`.

- `Missing Gemini API key`:
  - Set `GEMINI_API_KEY` (preferred) or `GCP_API_KEY` in `backend/.env`.

## 9. Stop / Reset

Stop services:

```bash
cd <repo-root>
docker compose stop backend postgres
```

Stop and remove containers:

```bash
cd <repo-root>
docker compose down
```

Reset database volume (destructive):

```bash
cd <repo-root>
docker compose down -v
docker compose up -d postgres
```
