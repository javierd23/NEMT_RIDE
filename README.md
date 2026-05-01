# NEMT Ride — Non-Emergency Medical Transport API

A RESTful API built with **Django 6** and **Django REST Framework** for managing non-emergency medical transport rides. The system supports multiple user roles (rider, driver, dispatcher, admin), JWT-based authentication, ride lifecycle management, GPS-based distance sorting, and full test coverage.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Environment Variables](#environment-variables)
- [Database & Migrations](#database--migrations)
- [Seed Data](#seed-data)
- [Running the Server](#running-the-server)
- [Running Tests](#running-tests)
- [API Endpoints](#api-endpoints)
- [Authentication](#authentication)
- [Filtering, Ordering & Pagination](#filtering-ordering--pagination)
- [API Documentation (Swagger)](#api-documentation-swagger)
- [Django Admin](#django-admin)
- [Design Decisions](#design-decisions)
- [Known Limitations & Future Work](#known-limitations--future-work)

---

## Tech Stack

| Package | Version | Purpose |
|---|---|---|
| Python | 3.13.2 | Runtime |
| Django | 6.0.4 | Web framework |
| djangorestframework | 3.17.1 | REST API layer |
| djangorestframework-simplejwt | 5.5.1 | JWT auth + token blacklist |
| django-filter | 25.2 | QuerySet filtering |
| drf-spectacular | 0.29.0 | OpenAPI 3 / Swagger docs |
| django-debug-toolbar | 6.3.0 | SQL query inspection (DEBUG only) |
| python-dotenv | 1.2.2 | `.env` file loading |

---

## Project Structure

```
NEMT_ride/
├── myvenv/                     # Virtual environment (not committed)
└── nemt_ride/                  # Django project root
    ├── manage.py
    ├── .env                    # Secret config (not committed)
    ├── requirements.txt
    ├── nemt_ride/              # Project settings package
    │   ├── settings.py
    │   ├── urls.py
    │   └── permissions.py      # Custom IsAdmin permission
    ├── user_auth/              # Authentication app
    │   ├── models.py           # User, UserRoles
    │   ├── serializers.py
    │   ├── views.py            # SignUp, Login, Logout
    │   ├── urls.py
    │   ├── admin.py
    │   ├── tests.py
    │   └── management/commands/
    │       ├── seed_roles.py
    │       └── seed_user.py
    └── ride/                   # Ride management app
        ├── models.py           # Ride, RideStatus, Ride_Event
        ├── serializers.py
        ├── views.py            # RideViewSet
        ├── filters.py          # RideFilter
        ├── urls.py
        ├── admin.py
        ├── tests.py
        └── management/commands/
            ├── seed_ride_status.py
            └── seed_ride.py
```

---

## Prerequisites

- Python 3.11+ (tested on 3.13.2)
- Git

---

## Installation & Setup

```bash
# 1. Clone the repository
git clone git@github.com:javierd23/NEMT_RIDE.git
cd NEMT_RIDE

# 2. Create and activate a virtual environment
python -m venv myvenv

# Windows
myvenv\Scripts\activate
# macOS / Linux
source myvenv/bin/activate

# 3. Install dependencies
pip install -r nemt_ride/requirements.txt

# 4. Create the .env file (see next section)
```

---

## Environment Variables

Create a file at `nemt_ride/.env` with the following content:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

**Generating a secret key:**

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

> `.env` is listed in `.gitignore` and must never be committed.

---

## Database & Migrations

SQLite is used in development (zero configuration required).

```bash
cd nemt_ride
python manage.py migrate
```

---

## Seed Data

Seed commands must be run in order. Each command is idempotent (`get_or_create`) and safe to re-run.

```bash
# 1. Create roles: rider, driver, dispatcher, admin
python manage.py seed_roles

# 2. Create 3 riders, 3 drivers, 1 admin
python manage.py seed_user

# 3. Create ride statuses: requested, en-route, picked-up, started, dropped-off, cancelled
python manage.py seed_ride_status

# 4. Create sample rides with GPS coords and ride events
python manage.py seed_ride
```


## Running the Server

```bash
cd nemt_ride
python manage.py runserver
```

Server starts at `http://127.0.0.1:8000/`.

---

## Running Tests

```bash
cd nemt_ride

# Run all tests
python manage.py test

# Run a specific app
python manage.py test user_auth
python manage.py test ride

# Verbose output
python manage.py test --verbosity=2
```

**Current coverage: 54 tests, 0 failures.**

| App | Test class | Tests |
|---|---|---|
| user_auth | `SignUpTest` | 201 response, tokens, user in DB, role protection, duplicate email, validation |
| user_auth | `LoginTest` | 200 response, tokens, wrong password, inactive user, missing fields |
| user_auth | `LogoutTest` | Blacklist on logout, reuse rejected, invalid token, unauthenticated |
| ride | `RidePermissionsTest` | Unauthenticated → 401, non-admin roles → 403, admin → 200 |
| ride | `RideListTest` | Count, pagination shape, response fields, string status, default ordering |
| ride | `RideFilterTest` | Filter by status and rider email (case-insensitive, empty results) |
| ride | `RideOrderingTest` | Ascending and descending by `pickup_time` |
| ride | `RideDistanceAnnotationTest` | `distance_to_pickup` with/without lat/lon, distance ordering, invalid/partial params |
| ride | `RideTodaysEventsTest` | Recent events included, >24h events excluded, empty list |
| ride | `RideCRUDTest` | Retrieve, create, partial update, delete |

---

## API Endpoints

All endpoints are prefixed with `/api/v1/`.

### Auth

| Method | Endpoint | Auth required | Description |
|---|---|---|---|
| POST | `/api/v1/auth/signup/` | No | Register a new user (role defaults to rider) |
| POST | `/api/v1/auth/login/` | No | Login with email + password, receive JWT tokens |
| POST | `/api/v1/auth/logout/` | Yes | Blacklist the provided refresh token |
| POST | `/api/v1/auth/token/` | No | Obtain JWT token pair (SimpleJWT default view) |
| POST | `/api/v1/auth/token/refresh/` | No | Refresh an access token |
| POST | `/api/v1/auth/token/verify/` | No | Verify a token is still valid |

### Rides

| Method | Endpoint | Auth required | Description |
|---|---|---|---|
| GET | `/api/v1/rides/` | Admin | List all rides (paginated, filterable, sortable) |
| POST | `/api/v1/rides/` | Admin | Create a ride |
| GET | `/api/v1/rides/{id}/` | Admin | Retrieve a ride |
| PUT | `/api/v1/rides/{id}/` | Admin | Full update a ride |
| PATCH | `/api/v1/rides/{id}/` | Admin | Partial update a ride |
| DELETE | `/api/v1/rides/{id}/` | Admin | Delete a ride |

---

## Authentication

The API uses **JWT Bearer tokens** via `djangorestframework-simplejwt`.

**Token lifetimes:**
- Access token: 30 minutes
- Refresh token: 7 days (rotated on each refresh, old token blacklisted)

**Usage — include the access token in the Authorization header:**

```
Authorization: Bearer <access_token>
```

**Rate limits:**
- Anonymous: 50 requests/minute
- Authenticated: 100 requests/minute

---

## Filtering, Ordering & Pagination

### Filtering (GET `/api/v1/rides/`)

| Query param | Description | Example |
|---|---|---|
| `status` | Filter by ride status (case-insensitive) | `?status=requested` |
| `rider_email` | Filter by rider's email (case-insensitive) | `?rider_email=rider1@nemt.com` |

### Ordering

| Query param | Options | Default |
|---|---|---|
| `ordering` | `pickup_time`, `-pickup_time`, `distance_to_pickup` | `-pickup_time` |

### Distance sorting

Pass `lat` and `lon` query parameters to annotate each ride with its Haversine distance (km) from your GPS position. This also enables `?ordering=distance_to_pickup`.

```
GET /api/v1/rides/?lat=25.7617&lon=-80.1918&ordering=distance_to_pickup
```

### Pagination

Default page size: 10 results. Use `?page=2` to navigate.

Response shape:

```json
{
  "count": 42,
  "next": "http://127.0.0.1:8000/api/v1/rides/?page=2",
  "previous": null,
  "results": [...]
}
```

---

## API Documentation (Swagger)

Available only when `DEBUG=True`:

| URL | Description |
|---|---|
| `/api/docs/` | Swagger UI (interactive) |
| `/api/redoc/` | ReDoc |
| `/api/schema/` | Raw OpenAPI 3 schema (JSON/YAML) |

---

## Django Admin

Access the admin panel at `/admin/`. Log in with the seeded admin credentials (`admin@nemt.com` / `Admin1pass!`) or a superuser you create:

```bash
python manage.py createsuperuser
```

**Registered models:**

- `UserRoles` — list and search roles
- `User` — full CRUD with role/permission fieldsets, searchable by email
- `RideStatus` — list and search statuses
- `Ride` — list filtered by status, searchable by rider/driver email, inline ride events
- `Ride_Event` — standalone searchable list of all ride events

---

## Design Decisions

### Custom User model with role as a ForeignKey

`UserRoles` is a separate model rather than a `CharField` with choices. This makes it trivial to add new roles in the future without a schema migration, and it enables filtering users by role at the DB level.

The custom primary key is `id_user` (AutoField) instead of Django's default `id`. This required explicitly setting `USER_ID_FIELD = 'id_user'` and `USER_ID_CLAIM = 'user_id'` in `SIMPLE_JWT` — without this, JWT authentication raises `'User' object has no attribute 'id'`.

### Role defaults to rider on signup

New users always receive the rider role (FK default=3). The `role` field is intentionally excluded from `SignUpSerializer` to prevent privilege escalation via the API — a user cannot self-assign admin or driver roles at registration.

### Ride status as a ForeignKey

Same rationale as `UserRoles`: a separate `RideStatus` table is more maintainable than hard-coded choices and supports future extensions without migrations.

### 2-query ride list optimization

The `GET /api/v1/rides/` endpoint always executes exactly two data queries regardless of page size:

1. `SELECT` rides + joined status, rider, driver via `select_related`
2. `SELECT` ride events from the last 24 hours via `Prefetch(to_attr='todays_ride_events')`

A third `COUNT(*)` query is added by the paginator. This avoids the N+1 problem that would arise from loading related objects inside the serializer loop.

Only the last 24 hours of ride events are fetched (not full history). This is intentional — the endpoint is designed for operational dashboards where only recent activity is relevant.

### Haversine distance computed in the database

Rather than loading all ride coordinates into Python and computing distances in memory, the Haversine formula is expressed using Django ORM functions (`ACos`, `Sin`, `Cos`, `Radians`) and pushed down to SQLite. This keeps the queryset sortable and paginatable at the DB level — a Python-side approach would require loading the entire table before sorting.

### Token blacklist on logout

`BLACKLIST_AFTER_ROTATION = True` combined with an explicit `token.blacklist()` on the logout endpoint ensures refresh tokens are invalidated server-side. A blacklisted token rejected on reuse with a meaningful `TokenError` message (e.g. `"Token is blacklisted"`).

### Debug-only tooling

Swagger/ReDoc, `django-debug-toolbar`, and the SQL console logger are all guarded by `if DEBUG`. They are never exposed in production and do not appear in `INSTALLED_APPS` or `urlpatterns` when `DEBUG=False`.

### URL versioning

`URLPathVersioning` with `DEFAULT_VERSION = 'v1'` is used. All endpoints live under `/api/v1/`. This makes it straightforward to introduce a `/api/v2/` prefix for breaking changes without affecting existing clients.

---

## Known Limitations & Future Work

- **SQLite only** — The Haversine annotation uses `ACos`/`Sin`/`Cos`/`Radians` which work in SQLite for development, but production deployments should use PostgreSQL with `PostGIS` for more robust spatial queries.
- **Admin-only ride access** — Currently only admin users can access ride CRUD. A future iteration could introduce role-scoped views (riders see their own rides, drivers see assigned rides).
- **No email verification** — User signup does not require email confirmation. This is intentional for the initial API scope.
- **No refresh token endpoint for signup/login** — The login and signup responses return a refresh token in the body. In a production system consider setting the refresh token in an `HttpOnly` cookie to mitigate XSS exposure.
- **Dispatcher role** — The `dispatcher` role exists in the seed data but has no dedicated endpoints or permissions yet.
