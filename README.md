# Reddit Clone API

A Django REST Framework backend for a Reddit-style social app: user accounts with OTP email verification, posts, comments, likes, and Redis-cached recent feeds.

## Tech stack

| Layer | Choice |
| --- | --- |
| Framework | Django 6 + Django REST Framework |
| Auth | JWT (`djangorestframework-simplejwt`) |
| Database | PostgreSQL 17 |
| Cache | Redis 7 |
| Docs | Swagger / ReDoc (`drf-yasg`) |
| Runtime | Docker Compose (Python 3.12) |

## Features

**Auth (`core`)**
- Register with username, email, password (optional avatar URL)
- Email OTP verification and resend
- JWT login / refresh (login throttled to 10/hour)
- Delete account

**Social (`social`)**
- Create, edit, and delete posts (text + optional image)
- Like / unlike posts
- Add and delete comments (nested replies supported in the model)
- List recent posts (last hour, Redis-cached), latest posts, and posts by user

**In progress**
- Follow / unfollow (model exists; API pending)
- Feed ranking (newer posts, tags, following-based feed, reportable content)
- Nginx + CDN for static/media

## Project structure

```
reddit-clone/
├── docker-compose.yml      # web + postgres + redis
├── Dockerfile
├── requirements.txt
├── .env                    # local secrets (not committed)
└── src/
    ├── manage.py
    ├── core/               # users, OTP, following model
    ├── social/             # posts, comments, reports
    ├── feed/               # feed app (scaffold)
    ├── templates/email/    # OTP email template
    └── src/                # Django project settings & URLs
```

## Quick start (Docker)

**Prerequisites:** Docker and Docker Compose.

1. Create a `.env` in the repo root (see [Environment variables](#environment-variables)).
2. Start services:

```bash
docker compose up --build
```

3. In another terminal, run migrations:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser   # optional
```

4. Open:
   - API: http://localhost:8000
   - Swagger: http://localhost:8000/swagger/
   - ReDoc: http://localhost:8000/redoc/
   - Admin: http://localhost:8000/admin/

## Local development (without Docker for the app)

**Prerequisites:** Python 3.12+, PostgreSQL, Redis.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Point `.env` at your local Postgres and Redis (`DB_HOST=localhost`, `REDIS_URL=redis://127.0.0.1:6379/1`), then:

```bash
cd src
python manage.py migrate
python manage.py runserver
```

## Environment variables

Create `.env` at the repo root. Example:

```env
DEBUG=1
ALLOWED_HOSTS=localhost,127.0.0.1

# Postgres (used by Docker Compose and Django)
POSTGRES_DB=reddit
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/1
RECENT_POSTS_CACHE_TTL=60

# Email (OTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=you@example.com
EMAIL_HOST_PASSWORD=your_app_password
```

For local (non-Docker) runs, set `DB_HOST=localhost` and `REDIS_URL=redis://127.0.0.1:6379/1`.

## API overview

All JSON unless noted. Authenticated routes expect:

```http
Authorization: Bearer <access_token>
```

### Core — `/core/`

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `POST` | `/core/api/register/` | No | Create account + send OTP |
| `POST` | `/core/api/verify-otp/` | No | Verify email OTP |
| `POST` | `/core/api/resend-otp/` | No | Resend OTP |
| `POST` | `/core/api/token/` | No | Obtain JWT pair |
| `POST` | `/core/api/token/refresh/` | No | Refresh access token |
| `POST` | `/core/api/delete-acc/` | Yes | Delete account (password required) |

### Social — `/social/`

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `POST` | `/social/api/create-post/` | Yes | Create post |
| `PUT/PATCH` | `/social/api/edit-post/<uuid>/` | Yes | Update own post |
| `DELETE` | `/social/api/delete-post/<uuid>/` | Yes | Delete own post |
| `POST` | `/social/api/like-post/<uuid>/` | Yes | Like post |
| `POST` | `/social/api/unlike-post/<uuid>/` | Yes | Unlike post |
| `POST` | `/social/api/add-comment/<uuid>/` | Yes | Comment on post |
| `DELETE` | `/social/api/delete-comment/<uuid>/` | Yes | Delete comment |
| `GET` | `/social/api/recent-posts/` | Yes | Posts from the last hour (cached) |
| `GET` | `/social/api/latest-posts/` | Yes | Latest posts |
| `GET` | `/social/api/user-posts/<user_id>/` | Yes | Posts by user |

Interactive schemas and try-it-out live at `/swagger/`.

## Typical auth flow

1. `POST /core/api/register/` with `username`, `email`, `password`
2. Confirm OTP via `POST /core/api/verify-otp/`
3. `POST /core/api/token/` with username/password → `access` + `refresh`
4. Call social endpoints with `Authorization: Bearer <access>`

## License

BSD (as noted in the OpenAPI schema). Private use unless you publish otherwise.
