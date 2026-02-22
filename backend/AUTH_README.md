# Authentication System

JWT-based authentication for the InvoiceGuard API and frontend.

## Overview

- **Access tokens**: Short-lived (30 min), used for API requests via `Authorization: Bearer <token>` header
- **Refresh tokens**: Long-lived (7 days), used to obtain new access/refresh token pairs
- **Password hashing**: bcrypt via passlib
- **JWT signing**: HS256 via python-jose, using `SECRET_KEY` from environment

## API Endpoints

All auth endpoints are under `/api/v1/auth`.

### Register a new user

```
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@company.com",
  "password": "securepassword",
  "full_name": "John Doe",
  "company_name": "Acme Corp"    // optional
}
```

**Response (201):**

```json
{
  "id": "uuid",
  "email": "user@company.com",
  "full_name": "John Doe",
  "company_name": "Acme Corp",
  "is_active": true,
  "created_at": "2026-02-22T12:00:00Z"
}
```

**Errors:** 409 if email already registered.

### Login

```
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@company.com",
  "password": "securepassword"
}
```

**Response (200):**

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

**Errors:** 401 if invalid credentials or account disabled.

### Refresh tokens

```
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ..."
}
```

**Response (200):** Same shape as login response (new token pair).

**Errors:** 401 if refresh token is invalid or expired.

### Get current user

```
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

**Response (200):** Same shape as register response.

**Errors:** 401 if token is invalid/expired, 403 if no token provided.

## Protected Routes

All API endpoints except `/api/v1/auth/*` require a valid access token. Send the token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Without a valid token, protected endpoints return **403** (missing token) or **401** (invalid/expired token).

## Token Lifecycle

```
1. User registers    → POST /auth/register  → User created in DB
2. User logs in      → POST /auth/login     → Access + Refresh tokens
3. API requests      → GET /invoices/       → Include Bearer token
4. Token expires     → POST /auth/refresh   → New token pair
5. Refresh expires   → User must log in again
```

## Environment Variables

| Variable                      | Description       | Default                      |
| ----------------------------- | ----------------- | ---------------------------- |
| `SECRET_KEY`                  | JWT signing key   | `super_insecure_default_key` |
| `JWT_ALGORITHM`               | JWT algorithm     | `HS256`                      |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL  | `30`                         |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | Refresh token TTL | `7`                          |

**Important:** Change `SECRET_KEY` to a strong random value in production.

## Frontend Integration

The frontend stores tokens in `localStorage` under the key `invoiceguard.auth.tokens`.

- On app load, the `AuthProvider` attempts to restore the session by calling `GET /auth/me` with the stored access token
- If the access token is expired, it automatically tries to refresh using the stored refresh token
- If both tokens are invalid, the user is redirected to the sign-in page
- All protected routes are wrapped in `` which checks auth state
- The extraction API call includes the Bearer token automatically

## Backend Architecture

```
core/security.py     → hash_password, verify_password, create/decode tokens
models/user.py       → User SQLAlchemy model (UUID PK, email unique)
repositories/user.py → UserRepository with get_by_email()
schemas/auth.py      → Pydantic request/response models
services/auth.py     → AuthService (register, login, refresh, get_current_user)
core/dependencies.py → get_current_user FastAPI dependency (Bearer token extraction)
api/routers/auth.py  → Auth API endpoints
```

All existing routers are protected via `dependencies=[Depends(get_current_user)]` at the router level.
