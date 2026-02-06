# Deployment Guide

This guide covers deploying the FarmLokal backend to production.

## 📋 Prerequisites

- Docker & Docker Compose
- PostgreSQL database
- Redis instance
- Google OAuth credentials
- Domain name with SSL certificate

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/Derisionn/hysteresis-assignment.git
cd hysteresis-assignment/farmlokal-backend
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your production values
```

### 3. Start Services

```bash
docker-compose up -d
```

### 4. Run Migrations

```bash
docker-compose exec app alembic upgrade head
```

### 5. Seed Database (Optional)

```bash
docker-compose exec app python scripts/seed_data.py
```

## 🔧 Production Configuration

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@postgres:5432/farmlokal

# Redis
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=your-super-secret-key-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# OAuth
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# External API
EXTERNAL_API_URL=https://api.external-service.com
EXTERNAL_API_TIMEOUT=30

# Caching
CACHE_ENABLED=true
CACHE_TTL_SECONDS=300

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Docker Compose Production

```yaml
version: '3.8'

services:
  app:
    build: .
    restart: always
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - postgres
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  postgres:
    image: postgres:15-alpine
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

## 🔒 Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Use strong database passwords
- [ ] Enable HTTPS/TLS
- [ ] Configure CORS properly
- [ ] Set up firewall rules
- [ ] Enable rate limiting
- [ ] Review OAuth redirect URIs
- [ ] Set up monitoring/alerting

## 📊 Monitoring

### Health Checks

```bash
# Basic health
curl https://api.yourdomain.com/api/v1/health

# Detailed health
curl https://api.yourdomain.com/api/v1/health/detailed

# Kubernetes probes
curl https://api.yourdomain.com/api/v1/health/ready
curl https://api.yourdomain.com/api/v1/health/live
```

### Metrics

Monitor these key metrics:
- Response time (P50, P95, P99)
- Error rate
- Cache hit rate
- Circuit breaker state
- Database connection pool
- Memory/CPU usage

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check database connectivity
docker-compose exec app python -c "from app.db.base import engine; engine.connect()"
```

### Redis Connection Issues

```bash
# Check Redis connectivity
docker-compose exec redis redis-cli ping
```

### OAuth Issues

1. Verify redirect URI matches Google Console
2. Check client ID and secret
3. Ensure HTTPS in production

### Performance Issues

1. Check cache hit rate: `/api/v1/health/detailed`
2. Review database indexes
3. Monitor circuit breaker state
4. Check rate limiting logs

## 🔄 Updates & Rollbacks

### Update Application

```bash
git pull origin main
docker-compose build
docker-compose up -d
docker-compose exec app alembic upgrade head
```

### Rollback

```bash
git checkout <previous-commit>
docker-compose build
docker-compose up -d
docker-compose exec app alembic downgrade -1
```

## 📈 Scaling

### Horizontal Scaling

Run multiple app instances behind a load balancer:

```yaml
services:
  app:
    deploy:
      replicas: 3
```

### Database Scaling

- Enable read replicas
- Use connection pooling (already configured)
- Consider database sharding for very large datasets

### Cache Scaling

- Use Redis Cluster for high availability
- Configure Redis persistence (AOF/RDB)

## 🔐 Backup & Recovery

### Database Backup

```bash
# Backup
docker-compose exec postgres pg_dump -U postgres farmlokal > backup.sql

# Restore
docker-compose exec -T postgres psql -U postgres farmlokal < backup.sql
```

### Redis Backup

```bash
# Backup
docker-compose exec redis redis-cli SAVE
docker cp farmlokal-backend_redis_1:/data/dump.rdb ./redis-backup.rdb

# Restore
docker cp ./redis-backup.rdb farmlokal-backend_redis_1:/data/dump.rdb
docker-compose restart redis
```

## 📞 Support

For issues or questions:
- GitHub Issues: https://github.com/Derisionn/hysteresis-assignment/issues
- Email: support@farmlokal.com
