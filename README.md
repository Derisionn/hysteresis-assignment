# FarmLokal Backend API

Production-ready backend system with OAuth authentication, high-performance product APIs, Redis caching, and reliability patterns.

## 🚀 Features

- **OAuth 2.0 Authentication** - Google OAuth integration with JWT tokens
- **High-Performance Product API** - Cursor-based pagination, filtering, sorting with Redis caching
- **Reliability Patterns** - Circuit breaker, retry logic, rate limiting
- **External API Integration** - Resilient HTTP client with fallback mechanisms
- **Comprehensive Testing** - Unit, integration, and load tests
- **Docker Support** - Full containerization with Docker Compose

## 📋 Prerequisites

- Docker Desktop (for Windows)
- Git
- 16GB RAM recommended
- Internet connection

## 🛠️ Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Derisionn/hysteresis-assignment.git
cd farmlokal-backend
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and update the following:
- `JWT_SECRET_KEY` - Generate a secure random string
- `GOOGLE_CLIENT_ID` - Your Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Your Google OAuth client secret

### 3. Start Services with Docker Compose

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database (port 5432)
- Redis cache (port 6379)
- FastAPI application (port 8000)
- Mock external API (port 8001)

### 4. Run Database Migrations

```bash
docker-compose exec app alembic upgrade head
```

### 5. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📚 API Endpoints

### Authentication
- `GET /api/v1/auth/login/google` - Initiate Google OAuth
- `GET /api/v1/auth/callback/google` - OAuth callback
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/me` - Get current user

### Products
- `GET /api/v1/products` - List products (with caching)
- `GET /api/v1/products/{id}` - Get product details
- `POST /api/v1/products` - Create product (admin only)
- `PUT /api/v1/products/{id}` - Update product (admin only)
- `DELETE /api/v1/products/{id}` - Delete product (admin only)

### Health
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed system status

## 🔧 Development

### Running Locally (without Docker)

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

## 📚 API Documentation

### Authentication Endpoints

#### Google OAuth Login
```bash
GET /api/v1/auth/login/google
```
Redirects to Google OAuth consent page.

#### OAuth Callback
```bash
GET /api/v1/auth/callback/google
```
Handles OAuth callback and returns JWT tokens.

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 900
}
```

#### Refresh Token
```bash
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGc..."
}
```

#### Get Current User
```bash
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00"
}
```

#### Logout
```bash
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
```

---

### Product Endpoints

#### List Products
```bash
GET /api/v1/products?category=Vegetables&min_price=2.00&max_price=5.00&sort_by=price&sort_order=asc&limit=20
```

**Query Parameters:**
- `category` (optional): Filter by category
- `min_price` (optional): Minimum price filter
- `max_price` (optional): Maximum price filter
- `availability` (optional): Filter by availability (true/false)
- `search` (optional): Search in name and description
- `sort_by` (optional): Sort field (name, price, created_at)
- `sort_order` (optional): Sort order (asc, desc)
- `limit` (optional): Page size (1-100, default: 20)
- `cursor` (optional): Pagination cursor

**Response:**
```json
{
  "products": [
    {
      "id": "uuid",
      "name": "Organic Tomatoes",
      "description": "Fresh organic tomatoes",
      "price": "3.99",
      "category": "Vegetables",
      "stock_quantity": 150,
      "availability": true,
      "image_url": "https://example.com/image.jpg",
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ],
  "total": 1,
  "page_size": 20,
  "cursor": "eyJpZCI6IjEyMyIsInZhbHVlIjoiMjAyNC0wMS0wMSJ9",
  "has_more": false
}
```

#### Get Product
```bash
GET /api/v1/products/{product_id}
```

#### Create Product (Admin Only)
```bash
POST /api/v1/products
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "Fresh Spinach",
  "description": "Organic baby spinach",
  "price": 3.99,
  "category": "Vegetables",
  "stock_quantity": 100,
  "availability": true,
  "image_url": "https://example.com/spinach.jpg"
}
```

#### Update Product (Admin Only)
```bash
PUT /api/v1/products/{product_id}
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "price": 4.99,
  "stock_quantity": 80
}
```

#### Delete Product (Admin Only)
```bash
DELETE /api/v1/products/{product_id}
Authorization: Bearer <admin_token>
```

---

### Health Check Endpoints

#### Basic Health
```bash
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00"
}
```

#### Detailed Health
```bash
GET /api/v1/health/detailed
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00",
  "services": {
    "database": {
      "status": "healthy",
      "message": "Database connection successful"
    },
    "cache": {
      "status": "healthy",
      "message": "Redis connection successful",
      "stats": {
        "hits": 1000,
        "misses": 200,
        "hit_rate": 83.33
      }
    },
    "external_api": {
      "status": "healthy",
      "circuit_breaker": {
        "name": "external_api",
        "state": "closed",
        "failure_count": 0,
        "failure_threshold": 5
      }
    }
  },
  "system": {
    "cpu_percent": 25.4,
    "memory_percent": 62.1,
    "disk_percent": 45.8
  }
}
```

#### Readiness Probe
```bash
GET /api/v1/health/ready
```

#### Liveness Probe
```bash
GET /api/v1/health/live
```

---

## 🧪 Testing

### Run All Tests
```bash
docker-compose exec app pytest -v
```

### Run Specific Test Suite
```bash
# Unit tests
docker-compose exec app pytest tests/unit/ -v

# Integration tests
docker-compose exec app pytest tests/integration/ -v

# E2E tests
docker-compose exec app pytest tests/e2e/ -v

# Performance tests
docker-compose exec app pytest tests/performance/ -v -s
```

### Test Coverage
```bash
docker-compose exec app pytest --cov=app --cov-report=html
```

### Load Testing

```bash
locust -f tests/load/test_products.py --host=http://localhost:8000
```

## 🔐 OAuth Setup (Google)

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name (e.g., "FarmLokal Backend")
4. Click "Create"

### Step 2: Enable Google+ API

1. In the left sidebar, go to "APIs & Services" → "Library"
2. Search for "Google+ API"
3. Click on it and press "Enable"

### Step 3: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client ID"
3. If prompted, configure OAuth consent screen:
   - User Type: External
   - App name: FarmLokal
   - User support email: your email
   - Developer contact: your email
   - Click "Save and Continue"
4. Application type: Web application
5. Name: FarmLokal Backend
6. Authorized redirect URIs:
   - Add: `http://localhost:8000/api/v1/auth/callback/google`
   - For production, add your production URL
7. Click "Create"

### Step 4: Configure Environment Variables

1. Copy the Client ID and Client Secret
2. Open `.env` file (copy from `.env.example` if needed)
3. Update:
   ```env
   GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret-here
   ```

### Step 5: Test OAuth Flow

1. Start the application: `docker-compose up`
2. Visit: http://localhost:8000/api/v1/auth/login/google
3. You should be redirected to Google login
4. After login, you'll receive JWT tokens

---

## 📊 Architecture

```
farmlokal-backend/
├── app/                    # Application code
│   ├── api/               # API routes
│   ├── core/              # Core utilities (cache, security, circuit breaker)
│   ├── db/                # Database models and session
│   ├── middleware/        # Custom middleware
│   ├── schemas/           # Pydantic models
│   └── services/          # Business logic
├── migrations/            # Alembic migrations
├── mock_services/         # Mock external API
├── tests/                 # Test suite
└── docker-compose.yml     # Docker configuration
```

## 🎯 Performance Targets

- Product listing (cached): < 50ms p95
- Product listing (uncached): < 300ms p95
- Authentication: < 200ms p95
- Throughput: > 1000 req/sec
- Cache hit ratio: > 80%

## 📝 Commit History

This project follows atomic commit conventions:
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `test:` - Test additions/changes
- `chore:` - Maintenance tasks
- `perf:` - Performance improvements

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make atomic commits
4. Push to your fork
5. Create a Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For issues or questions, please open an issue on GitHub.

---

**Built with ❤️ for FarmLokal Backend Challenge**
