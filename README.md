# Online Cinema API

Online Cinema API is a FastAPI backend application for an online movie service.

The project includes user registration and authentication, movie management, shopping cart functionality, order creation, token cleanup with Celery, PostgreSQL support, Docker setup, and basic automated tests.

## Technologies

- Python 3.13
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Redis
- Celery
- Poetry
- Docker / Docker Compose
- Pytest
- Flake8
- GitHub Actions

## Features

### Authentication and users

- User registration
- Account activation by token
- Login with JWT access and refresh tokens
- Refresh access token
- User profile support
- Password hashing and validation

### Movies

- Get movie list
- Get movie details
- Filter movies by search, year and price
- Sort movies by id, year, rating or price
- Paginated movie list
- Movie management endpoints

### Cart

- Get current user's cart
- Add movie to cart
- Prevent adding the same movie twice
- Remove movie from cart
- Clear cart

### Orders

- Create order from cart
- Save movie price at the moment of order creation
- Calculate total order amount
- View current user's orders
- View order details
- Cancel pending order
- Mark order as paid
- Clear cart after order creation

### Background tasks

- Celery task for cleaning expired activation, password reset and refresh tokens
- Redis as Celery broker/backend

### Project infrastructure

- PostgreSQL support
- Alembic migrations
- Docker and Docker Compose setup
- Poetry dependency management
- Pytest tests
- Flake8 linting
- GitHub Actions CI workflow

## Project structure

```text
.
├── .github
│   └── workflows
│       └── main.yml
├── alembic
│   ├── versions
│   │   ├── 830c55ce9a47_seed_user_groups.py
│   │   ├── 48270b1408b0_create_movies_and_genres_tables.py
│   │   ├── ca2fb2763d26_create_accounts_tables.py
│   │   ├── d617cbaaacd9_create_orders_tables.py
│   │   └── db81f74d1e48_create_cart_tables.py
│   ├── env.py
│   ├── README
│   └── script.py.mako
├── app
│   ├── accounts
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   ├── dependencies.py
│   │   ├── models.py
│   │   ├── routes.py
│   │   ├── schemas.py
│   │   ├── services.py
│   │   └── token_cleanup.py
│   ├── carts
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── routes.py
│   │   ├── schemas.py
│   │   └── services.py
│   ├── movies
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── routes.py
│   │   ├── schemas.py
│   │   └── services.py
│   ├── orders
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── routes.py
│   │   ├── schemas.py
│   │   └── services.py
│   ├── security
│   │   ├── __init__.py
│   │   ├── passwords.py
│   │   └── tokens.py
│   ├── validators
│   │   ├── __init__.py
│   │   └── accounts.py
│   ├── __init__.py
│   └── main.py
├── db
│   ├── __init__.py
│   ├── dependencies.py
│   └── engine.py
├── tests
│   ├── conftest.py
│   ├── helpers.py
│   ├── test_accounts.py
│   ├── test_cart.py
│   └── test_orders.py
├── .dockerignore
├── .env.sample
├── .flake8
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── poetry.lock
├── pyproject.toml
└── README.md
```

### Main directories

- `app/accounts` — user registration, activation, login, refresh tokens, profile logic and token cleanup.
- `app/movies` — movie models, schemas, routes and movie list filtering/sorting logic.
- `app/carts` — cart models, routes and cart item management.
- `app/orders` — order creation, order statuses, payment and cancellation logic.
- `app/security` — password hashing and JWT token helpers.
- `app/validators` — custom validation logic.
- `db` — database engine and session dependency.
- `alembic` — database migrations.
- `tests` — basic tests for accounts, cart and orders.
- `.github/workflows` — GitHub Actions CI configuration.

## Project setup

### 1. Clone the repository

```bash
git clone https://github.com/anastasiiaoshega513/online-cinema-api.git
cd online-cinema-api
```

### 2. Install dependencies

```bash
poetry install --with dev
```

### 3. Create environment file

Create .env based on .env.example:
```bash
cp .env.sample .env
```
Fill in the required values:
```env
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
POSTGRES_HOST=db
POSTGRES_PORT=5432

DATABASE_URL=

SECRET_KEY=

CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
```
Example DATABASE_URL for Docker:
```env
DATABASE_URL=postgresql+asyncpg://online_cinema_user:online_cinema_password@db:5432/online_cinema_db
```
### Running locally with Poetry
```bash
poetry run uvicorn app.main:app --reload
```
Swagger documentation:
```text
http://127.0.0.1:8000/docs
```

### Running with Docker

Build and start containers:
```bash
docker compose up --build
```
The application will be available at:
```text
http://127.0.0.1:8000/docs
```
Stop containers:
```bash
docker compose down
```
Stop containers and remove database volume:
```bash
docker compose down -v
```

### Database migrations

Run migrations locally:
```bash
poetry run alembic upgrade head
```
In Docker, migrations are applied automatically before starting the web server.

### Tests

Run tests:
```bash
poetry run pytest
```
### Linting

Run flake8:
```bash
poetry run flake8 app tests
```

### CI

The project uses GitHub Actions to run:

- flake8
- pytest

Workflow file:
```text
.github/workflows/ci.yml
```
