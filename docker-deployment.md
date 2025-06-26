# Docker Deployment Guide

This guide explains how to deploy the Instagram Scraper API using Docker and Docker Compose.

## Prerequisites

- Docker 20.0+ installed
- Docker Compose 2.0+ installed
- OpenAI API key

## Quick Start (Development)

1. **Clone and prepare environment:**
```bash
git clone <repository>
cd instagram-scraper
cp env.example .env
```

2. **Set required environment variables:**
Edit `.env` file and set your OpenAI API key:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

3. **Start services:**
```bash
docker-compose up -d
```

4. **Test the API:**
```bash
curl http://localhost:5000/health
```

## Production Deployment

### 1. Environment Setup

Create production environment file:
```bash
cp .env.prod.example .env.prod
```

Edit `.env.prod` with your production values:
- Set a secure `SECRET_KEY` (generate with: `python -c "import secrets; print(secrets.token_hex(32))"`)
- Set your `OPENAI_API_KEY`
- Adjust rate limits as needed

### 2. Production Start

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 3. Behind Reverse Proxy (Recommended)

The production setup binds to localhost only. Use nginx or similar:

**nginx.conf example:**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeout for scraping operations
        proxy_read_timeout 120;
        proxy_connect_timeout 60;
    }
}
```

## Available Services

### Development (docker-compose.yml)
- **App**: http://localhost:5000
- **Redis**: localhost:6379

### Production (docker-compose.prod.yml)
- **App**: http://127.0.0.1:5000 (localhost only)
- **Redis**: 127.0.0.1:6379 (localhost only)

## Docker Commands

### Start Services
```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d

# With build (if you made changes)
docker-compose up -d --build
```

### Stop Services
```bash
docker-compose down

# With volume removal (clears Redis data)
docker-compose down -v
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f redis
```

### Monitor Services
```bash
# Service status
docker-compose ps

# Resource usage
docker stats
```

## API Usage

### Health Check
```bash
curl http://localhost:5000/health
```

### Scrape Instagram Post
```bash
curl -X POST http://localhost:5000/scrape \
  -H "Content-Type: application/json" \
  -d '{"instagram_url": "https://www.instagram.com/p/XXXXXXXXX/"}'
```

## Important: Crawl4AI Setup

The Docker setup includes the essential `crawl4ai-setup` command that:
- **Installs Playwright browsers**: Automatically installs Chromium, Firefox, and other browsers required for web crawling
- **Performs OS-level checks**: Verifies missing libraries on Linux systems are installed
- **Environment validation**: Confirms the environment is ready for web crawling operations

This setup step is **automatically handled** during the Docker build process, so no manual intervention is required. However, if you encounter browser-related errors, this setup ensures proper functionality.

> **Reference**: Based on [Crawl4AI Installation Documentation](https://docs.crawl4ai.com/core/installation/)

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | **Required** OpenAI API key |
| `SECRET_KEY` | auto | Flask secret key (set in production) |
| `REDIS_URL` | redis://redis:6379/0 | Redis connection URL |
| `DEFAULT_RATE_LIMIT` | 10 per minute | General API rate limit |
| `SCRAPE_RATE_LIMIT` | 5 per minute | Scraping endpoint rate limit |
| `SCRAPE_TIMEOUT` | 60 | Scraping timeout (seconds) |
| `LOG_LEVEL` | INFO | Logging level |

### Volume Mounts

- `redis_data`: Redis persistence
- `./logs:/app/logs`: Application logs

## Troubleshooting

### Service Won't Start

1. **Check Docker status:**
```bash
docker-compose ps
```

2. **View detailed logs:**
```bash
docker-compose logs app
```

3. **Common issues:**
   - Missing `OPENAI_API_KEY` in `.env`
   - Port conflicts (5000 or 6379 already in use)
   - Insufficient permissions

### Redis Connection Issues

1. **Test Redis connectivity:**
```bash
docker-compose exec redis redis-cli ping
```

2. **Check Redis logs:**
```bash
docker-compose logs redis
```

### Scraping Failures

1. **Check application logs:**
```bash
docker-compose logs app | grep ERROR
```

2. **Common causes:**
   - Invalid OpenAI API key
   - Instagram rate limiting
   - Network connectivity issues
   - Chrome/ChromeDriver issues in container
   - **Crawl4AI setup issues**: If browser-related errors occur, ensure `crawl4ai-setup` completed successfully during build

### Performance Issues

1. **Monitor resource usage:**
```bash
docker stats
```

2. **Adjust resource limits** in production compose file

3. **Scale services:**
```bash
# Add more app instances
docker-compose up -d --scale app=3
```

## Security Considerations

### Production Checklist

- [ ] Set secure `SECRET_KEY`
- [ ] Use `.env.prod` with production values
- [ ] Enable Redis authentication (uncomment in `redis.conf`)
- [ ] Run behind reverse proxy with SSL
- [ ] Monitor logs for security issues
- [ ] Regular backup of Redis data
- [ ] Update Docker images regularly

### Network Security

The production setup:
- Binds services to localhost only
- Uses internal Docker networking
- Requires reverse proxy for external access

## Monitoring

### Health Checks

Both services include health checks:
- App: HTTP health endpoint
- Redis: ping command

### Log Management

Logs are stored in:
- Container logs: `docker-compose logs`
- Application logs: `./logs/` directory
- Redis logs: in Redis container

### Backup

**Redis data backup:**
```bash
# Create backup
docker-compose exec redis redis-cli BGSAVE

# Copy backup file
docker cp instagram-scraper-redis:/data/dump.rdb ./backup/
```

## Scaling

For high traffic, consider:

1. **Multiple app instances:**
```bash
docker-compose up -d --scale app=3
```

2. **Load balancer configuration**
3. **Redis clustering** for high availability
4. **Monitoring and alerting**

## Updates

To update the application:

1. **Pull latest code:**
```bash
git pull origin main
```

2. **Rebuild and restart:**
```bash
docker-compose down
docker-compose up -d --build
```

3. **Zero-downtime deployment** (with load balancer):
```bash
# Rolling update approach
docker-compose up -d --scale app=2
# Test new instances
docker-compose up -d --scale app=1 --force-recreate
``` 