# Stockee - Real-Time Stock Market Alert System

A Django REST API for real-time stock market alerts powered by LLM analysis. Track stocks, set custom alert rules, and receive intelligent notifications when market conditions match your criteria.

## Features

- **JWT Authentication** - Secure user registration, login, logout, and token refresh
- **Stock Tracking** - Monitor stocks with OHLCV data (Open, High, Low, Close, Volume)
- **Custom Alert Rules** - Set price thresholds, percentage changes, and volume spike alerts
- **LLM-Powered Analysis** - AI-generated explanations for price movements and triggered alerts
- **Multi-Channel Notifications** - Email and webhook support (Slack, Discord, etc.)
- **Role-Based Access** - Admin and user roles with different permission levels

## Tech Stack

- **Backend**: Django 5.2, Django REST Framework
- **Database**: PostgreSQL 16
- **Authentication**: JWT (Simple JWT)
- **Containerization**: Docker & Docker Compose
- **WSGI Server**: Gunicorn (production)

## Project Structure

```
stockee/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env                    # Environment variables (not in git)
└── stockee/
    ├── manage.py
    ├── stockee/            # Django project settings
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    └── core/               # Main application
        ├── models.py       # Database models
        ├── views.py        # API views
        ├── serializers.py  # DRF serializers
        └── urls.py         # URL routing
```

## Data Models

| Model | Description |
|-------|-------------|
| **Stock** | Stock ticker info (symbol, name, exchange, sector, currency) |
| **StockUpdate** | OHLCV price data with AI analysis |
| **UserProfile** | Extended user settings (role, timezone, webhook, alert limits) |
| **UserStockPreference** | User watchlist with notification preferences |
| **AlertRule** | User-defined alert conditions (price/percent thresholds) |
| **TriggeredAlert** | Records of fired alerts with LLM analysis |
| **NotificationLog** | Notification delivery tracking with retry support |
| **LLMUsageLog** | LLM API usage tracking (tokens, costs, latency) |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Git

### 1. Clone the repository

```bash
git clone https://github.com/Farouk-elouassif/stockee.git
cd stockee
```

### 2. Create environment file

```bash
cp .env.example .env
# Edit .env with your settings
```

Required environment variables:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True

DATABASE_NAME=stockee_db
DATABASE_USER=stockee_user
DATABASE_PASSWORD=your_secure_password
DATABASE_HOST=database
DATABASE_PORT=5432

ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_ENV=dev
```

### 3. Start the application

```bash
docker compose up -d --build
```

### 4. Run migrations

```bash
docker exec stockee_backend python manage.py migrate
```

### 5. Create a superuser (optional)

```bash
docker exec -it stockee_backend python manage.py createsuperuser
```

The API is now available at `http://localhost:8000`

## API Endpoints

### Authentication

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/auth/register/` | POST | No | Register new user |
| `/api/auth/login/` | POST | No | Login (returns JWT tokens) |
| `/api/auth/token/refresh/` | POST | No | Refresh access token |
| `/api/auth/logout/` | POST | Yes | Blacklist refresh token |
| `/api/auth/change-password/` | POST | Yes | Change password |
| `/api/auth/profile/` | GET | Yes | Get user profile |
| `/api/auth/profile/` | PATCH | Yes | Update user profile |

### Example Requests

**Register:**
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!"
  }'
```

**Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "password": "SecurePass123!"
  }'
```

**Access Protected Endpoint:**
```bash
curl -X GET http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer <access_token>"
```

**Refresh Token:**
```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<refresh_token>"}'
```

## Development

### Run locally without Docker

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_HOST=localhost
export DATABASE_PORT=5432
# ... other variables

# Run migrations
cd stockee
python manage.py migrate

# Start development server
python manage.py runserver
```

### View logs

```bash
docker compose logs -f stockee_backend
```

### Access database

```bash
docker exec -it stockee_db psql -U stockee_user -d stockee_db
```

### Run Django shell

```bash
docker exec -it stockee_backend python manage.py shell
```

## Production Deployment

Set in `.env`:
```env
DEBUG=False
DJANGO_ENV=prod
ALLOWED_HOSTS=your-domain.com
```

The Dockerfile automatically uses Gunicorn when `DJANGO_ENV=prod`.

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
