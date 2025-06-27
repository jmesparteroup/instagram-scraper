# Troubleshooting Guide

## Docker Build Errors

### Error: `pip install` fails with exit code 1

**Problem**: The pip installation step fails during Docker build with:
```
failed to solve: process "/bin/sh -c pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt" did not complete successfully: exit code: 1
```

**Root Cause**: This is typically caused by:
1. Missing system dependencies for package compilation
2. `crawl4ai` package requiring additional build tools
3. Network timeouts during large package downloads
4. Architecture-specific compilation issues

**Solutions**:

#### Option 1: Use the Production Dockerfile (Recommended)
The `Dockerfile.production` is designed to handle these issues with:
- Multi-stage build for cleaner production images
- All necessary system dependencies
- Extended timeouts for large packages
- Better error handling

In your Dokploy deployment, specify:
```yaml
build:
  context: .
  dockerfile: Dockerfile.production
```

#### Option 2: Enhanced Standard Dockerfile
The updated `Dockerfile` includes:
- Additional system dependencies (`build-essential`, `python3-dev`, etc.)
- Verbose pip installation for better debugging
- Individual package installation to identify problematic packages

#### Option 3: Debug Which Package is Failing
If you want to identify the specific failing package, use this temporary Dockerfile:

```dockerfile
FROM python:3.11-slim

# ... (same setup as before) ...

# Install packages one by one to identify the issue
RUN pip install --no-cache-dir flask==3.0.0 || echo "Flask failed"
RUN pip install --no-cache-dir openai==1.52.0 || echo "OpenAI failed"
RUN pip install --no-cache-dir crawl4ai==0.6.3 || echo "Crawl4AI failed"
# ... continue for each package
```

## Common Fixes

### 1. System Dependencies for Python Packages
```dockerfile
# Add these to your Dockerfile before pip install
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev
```

### 2. Increase pip Timeout
```dockerfile
RUN pip install --no-cache-dir --timeout=2000 crawl4ai==0.6.3
```

### 3. Platform-Specific Build
If you're on ARM (M1 Mac) deploying to AMD64:
```yaml
# In docker-compose.dokploy.yml
build:
  context: .
  dockerfile: Dockerfile.production
  platforms:
    - linux/amd64
```

### 4. Alternative Package Versions
If specific versions fail, try:
```
# In requirements.txt, replace problematic versions
crawl4ai>=0.6.0,<0.7.0  # Instead of exact version
```

## Deployment Issues

### 1. Playwright Browser Not Found
**Error**: `BrowserType.launch: Executable doesn't exist at /home/app/.cache/ms-playwright/chromium-1179/chrome-linux/chrome`

**Symptoms**: 
- Playwright suggests running `playwright install`
- Scraping fails with browser launch errors
- App logs show "Executable doesn't exist" errors

**Root Cause**: Playwright browsers need to be installed as root and made available system-wide before switching to the non-root user.

**Solution**:
1. **Rebuild with the updated Dockerfile** (the issue has been fixed in both `Dockerfile` and `Dockerfile.production`):
```bash
# For Dokploy deployment
docker-compose -f docker-compose.dokploy.yml build --no-cache scraper

# For local development
docker-compose build --no-cache scraper
```

2. **Verify browser installation** after rebuild:
```bash
# Check if browsers are installed
docker-compose -f docker-compose.dokploy.yml exec scraper playwright install --help

# List installed browsers
docker-compose -f docker-compose.dokploy.yml exec scraper playwright install --dry-run
```

3. **Manual browser installation** (if the above doesn't work):
```bash
# Install browsers manually
docker-compose -f docker-compose.dokploy.yml exec scraper playwright install chromium
```

**What was fixed**: The Dockerfiles now:
- Run `crawl4ai-setup` as root before switching users
- Explicitly install Playwright browsers with `playwright install chromium`
- Install system dependencies with `playwright install-deps`

### 2. Domain Not Accessible After Deployment

**Check DNS propagation**:
```bash
nslookup your-domain.com
dig your-domain.com
```

**Check Traefik logs in Dokploy**:
```bash
docker logs dokploy-traefik
```

### 3. Health Check Failures

**Verify application is starting**:
```bash
# In Dokploy logs, look for:
# "Starting Instagram Scraper API"
# "Configuration validated successfully"
```

**Common health check issues**:
- `OPENAI_API_KEY` not set
- Redis connection failure
- Port binding issues

### 4. Redis Connection Issues

**Check Redis service status**:
```bash
docker exec -it <redis-container> redis-cli ping
```

**Verify network connectivity**:
```bash
docker exec -it <app-container> curl http://redis:6379
```

## Environment Variable Issues

### Missing OPENAI_API_KEY
```bash
# In Dokploy dashboard, verify environment variables are set
# Check logs for: "Missing required environment variables: OPENAI_API_KEY"
```

### SECRET_KEY Generation
```python
# Generate a secure secret key
python -c "import secrets; print(secrets.token_hex(32))"
```

## Quick Diagnostics

### Test Local Build
```bash
# Test locally first
docker build -f Dockerfile.production -t test-scraper .
docker run --rm -p 5000:5000 -e OPENAI_API_KEY=test test-scraper
```

### Check Container Resources
```bash
# Monitor container resources
docker stats

# Check available disk space
df -h
```

### Verify Dependencies
```bash
# Inside running container
pip list | grep crawl4ai
crawl4ai-doctor  # If available
```

## When to Use Which Dockerfile

| Use Case | Dockerfile | Pros | Cons |
|----------|------------|------|------|
| **Local Development** | `Dockerfile` | Simple, fast builds | May have dependency issues |
| **Production/Dokploy** | `Dockerfile.production` | Robust, multi-stage, handles dependencies | Larger build time |
| **Debugging** | Modified with verbose flags | Shows exact error location | Slower builds |

## Getting Help

If you're still experiencing issues:

1. **Check build logs** in Dokploy dashboard for exact error
2. **Try production Dockerfile** first
3. **Verify all environment variables** are set
4. **Test locally** before deploying
5. **Check system resources** (disk space, memory)

### Useful Commands for Debugging

```bash
# View detailed Dokploy logs
docker service logs dokploy

# Check network connectivity
docker network ls | grep dokploy

# Inspect container
docker inspect <container-id>

# Force rebuild without cache
docker build --no-cache -f Dockerfile.production .
``` 