# FastAPI Team API

A backend API for organizations to manage users with roles. Supports registration, email verification, login with JWT, organizations, invitations, and RBAC.

## Features

- **Auth**: Register, verify email, login, logout, refresh token, forgot/reset password
- **Users**: Profile (GET/PATCH)
- **Organizations**: CRUD, members, invitations, role assignment
- **Invitations**: Accept invite by token (creates user if new)
- **RBAC**: Roles (admin/member) with permissions scoped per organization

## Setup

### 1. Virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment

```bash
cp .env.example .env
# Edit .env - set JWT_SECRET for production
```

### 3. Docker (Postgres + Adminer)

```bash
docker compose up -d
```

### 4. Migrations

```bash
alembic upgrade head
python -m scripts.seed_roles
```

## Run

```bash
uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- Docs: http://127.0.0.1:8000/docs
- Adminer: http://localhost:8080 (Postgres)

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Register |
| POST | `/api/v1/auth/verify-email` | Verify email |
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/auth/logout` | Logout |
| POST | `/api/v1/auth/refresh` | Refresh token |
| POST | `/api/v1/auth/forgot-password` | Request password reset |
| POST | `/api/v1/auth/reset-password` | Reset password |
| GET | `/api/v1/users/me` | Current user |
| PATCH | `/api/v1/users/me` | Update profile |
| POST | `/api/v1/organizations` | Create org |
| GET | `/api/v1/organizations` | List orgs |
| GET | `/api/v1/organizations/{id}` | Get org |
| PATCH | `/api/v1/organizations/{id}` | Update org |
| DELETE | `/api/v1/organizations/{id}` | Delete org (owner only) |
| GET | `/api/v1/organizations/{id}/members` | List members |
| POST | `/api/v1/organizations/{id}/invitations` | Invite by email |
| GET | `/api/v1/organizations/{id}/invitations` | List invitations |
| DELETE | `/api/v1/organizations/{id}/invitations/{inv_id}` | Revoke invitation |
| PATCH | `/api/v1/organizations/{id}/members/{user_id}/role` | Assign role |
| DELETE | `/api/v1/organizations/{id}/members/{user_id}` | Remove member |
| POST | `/api/v1/invitations/accept` | Accept invitation (public) |

## Project Structure

```
app/
├── main.py
├── config.py
├── database.py
├── models/       # User, Organization, Membership, Role, etc.
├── schemas/      # Pydantic schemas
├── routes/       # auth, users, organizations, invitations
├── auth/         # JWT, hashing, dependencies
└── services/     # mail
```
