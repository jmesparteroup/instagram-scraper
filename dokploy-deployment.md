# Dokploy Deployment Guide

This guide explains how to deploy the Instagram Scraper API on [Dokploy](https://docs.dokploy.com/docs), an open-source alternative to Heroku, Vercel, and Netlify.

## 📋 Prerequisites

- Dokploy server installed and running
- Domain name pointing to your Dokploy server
- OpenAI API key
- Git repository access

## 🚀 Quick Deployment

### 1. **Prepare Your Repository**

Ensure your repository contains the `docker-compose.dokploy.yml` file:

```bash
git add docker-compose.dokploy.yml
git commit -m "Add Dokploy deployment configuration"
git push origin main
```

### 2. **Create Application in Dokploy**

1. **Login to Dokploy Dashboard**
   - Access your Dokploy instance: `https://your-dokploy-domain.com`
   - Login with your credentials

2. **Create New Docker Compose Application**
   - Click **"Docker Compose"** → **"Create"**
   - **Name**: `instagram-scraper-api`
   - **Description**: `Instagram post scraping API with OpenAI integration`

3. **Configure Repository**
   - **Repository URL**: Your git repository URL
   - **Branch**: `main` (or your deployment branch)
   - **Docker Compose Path**: `docker-compose.dokploy.yml`

### 3. **Environment Variables**

In the Dokploy interface, add these environment variables:

| Variable | Value | Required |
|----------|-------|----------|
| `OPENAI_API_KEY` | `your_openai_api_key_here` | ✅ Yes |
| `SECRET_KEY` | `your-secure-flask-secret-key` | ✅ Yes |
| `DOMAIN_NAME` | `api.yourdomain.com` | ✅ Yes |
| `DEFAULT_RATE_LIMIT` | `10 per minute` | ❌ Optional |
| `SCRAPE_RATE_LIMIT` | `5 per minute` | ❌ Optional |
| `LOG_LEVEL` | `INFO` | ❌ Optional |

> **💡 Tip**: Generate a secure `SECRET_KEY` with: `python -c "import secrets; print(secrets.token_hex(32))"`

### 4. **Configure Domain**

1. **DNS Setup**
   - Add an A record pointing `api.yourdomain.com` to your Dokploy server IP
   - Wait for DNS propagation (up to 24 hours)

2. **Domain Configuration in Dokploy**
   - Go to **"Domains"** section
   - Click **"Create Domain"**
   - **Host**: `api.yourdomain.com`
   - **Container Port**: `5000` (matches our Flask app)
   - **Path**: `/`
   - **HTTPS**: ✅ Enabled
   - **Certificate**: `Let's Encrypt`

### 5. **Deploy the Application**

1. **Deploy**
   - Click **"Deploy"** button
   - Monitor deployment logs for any issues
   - Wait for successful completion

2. **Verify Deployment**
   ```bash
   curl https://api.yourdomain.com/health
   ```

   Expected response:
   ```json
   {
     "status": "healthy",
     "timestamp": "2024-01-01T12:00:00.000Z",
     "version": "1.0.0"
   }
   ```

## 🔧 Dokploy-Specific Configuration

### Key Changes from Standard Docker Compose

1. **Network Configuration**
   - Uses `dokploy-network` (external network managed by Dokploy)
   - Services communicate internally without exposing ports

2. **Volume Mounts**
   - Uses `../files/` prefix for persistent storage
   - Data persists across deployments

3. **Traefik Labels**
   - Automatic HTTPS with Let's Encrypt
   - Domain-based routing
   - HTTP to HTTPS redirect

4. **Port Configuration**
   - Uses `expose` instead of `ports`
   - Traefik handles external access

### File Structure in Dokploy

```
/your-app-folder/
├── docker-compose.dokploy.yml
├── Dockerfile
├── files/                     # Persistent storage
│   ├── logs/                 # Application logs
│   ├── redis-data/           # Redis persistence
│   └── redis.conf            # Redis configuration
├── app.py
├── config.py
└── requirements.txt
```

## 📊 Monitoring & Management

### Health Checks

Both services include health checks:
- **App**: HTTP endpoint at `/health`
- **Redis**: Redis ping command

### View Logs

In Dokploy dashboard:
1. Go to your application
2. Click **"Logs"** tab
3. Select service (`app` or `redis`)
4. View real-time or historical logs

### Scaling

To scale the application:
1. Go to **"Advanced"** settings
2. Adjust **"Replicas"** count
3. Deploy changes

## 🔒 Security Best Practices

### Environment Variables
- ✅ Store sensitive data in Dokploy environment variables
- ✅ Use strong `SECRET_KEY`
- ✅ Regularly rotate API keys

### Domain & SSL
- ✅ Use HTTPS only (automatic with Let's Encrypt)
- ✅ Configure proper domain pointing
- ✅ Enable HTTP to HTTPS redirect

### Rate Limiting
- ✅ Configure appropriate rate limits
- ✅ Monitor for abuse patterns
- ✅ Adjust limits based on usage

## 🚨 Troubleshooting

### Common Issues

#### 1. **Deployment Fails**
```bash
# Check logs in Dokploy dashboard
# Common causes:
- Missing environment variables
- Invalid docker-compose.yml syntax
- Build failures (check Dockerfile)
```

#### 2. **Domain Not Accessible**
```bash
# Verify DNS propagation
nslookup api.yourdomain.com

# Check Traefik configuration
docker logs dokploy-traefik
```

#### 3. **API Returns 500 Errors**
```bash
# Check application logs in Dokploy
# Common causes:
- Missing OPENAI_API_KEY
- Redis connection issues
- Crawl4AI setup problems
```

#### 4. **Redis Connection Failed**
```bash
# Check Redis service status in Dokploy
# Verify network connectivity between services
# Check redis.conf file exists in ../files/
```

### Debug Commands

```bash
# Check running containers
docker ps

# View Dokploy network
docker network ls | grep dokploy

# Check service logs
docker logs <container-name>

# Test internal connectivity
docker exec -it <app-container> curl http://redis:6379
```

## 🔄 Continuous Deployment

### Webhook Setup

1. **Get Webhook URL**
   - In Dokploy, go to **"Deployments"** tab
   - Copy the webhook URL

2. **Configure Git Webhook**
   
   **GitHub:**
   - Repository → Settings → Webhooks
   - Add webhook with copied URL
   - Select "Push events"

   **GitLab:**
   - Project → Settings → Webhooks
   - Add webhook with copied URL
   - Select "Push events"

3. **Automatic Deployments**
   - Push to your configured branch
   - Dokploy automatically deploys changes
   - Monitor deployment in dashboard

## 📈 Performance Optimization

### Resource Allocation
```yaml
# Add to docker-compose.dokploy.yml services
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '0.5'
    reservations:
      memory: 512M
      cpus: '0.25'
```

### Caching Strategy
- Redis for rate limiting (already configured)
- Consider adding application-level caching
- Use CDN for static assets if needed

### Monitoring
- Enable Dokploy monitoring features
- Set up alerts for high error rates
- Monitor resource usage patterns

## 🔧 Advanced Configuration

### Custom Traefik Middlewares

Add custom middleware for additional security:

```yaml
labels:
  - "traefik.http.middlewares.auth.basicauth.users=user:$$2y$$10$$..."
  - "traefik.http.routers.instagram-scraper-https.middlewares=auth"
```

### Database Persistence

For production, consider adding PostgreSQL:

```yaml
database:
  image: postgres:15-alpine
  environment:
    - POSTGRES_DB=instagram_scraper
    - POSTGRES_USER=${DB_USER}
    - POSTGRES_PASSWORD=${DB_PASSWORD}
  volumes:
    - ../files/postgres-data:/var/lib/postgresql/data
  networks:
    - dokploy-network
```

## 📚 Additional Resources

- [Dokploy Documentation](https://docs.dokploy.com/docs)
- [Traefik Configuration Guide](https://docs.dokploy.com/docs/core/core/domains)
- [Docker Compose Best Practices](https://docs.dokploy.com/docs/core/core/docker-compose)

## 🚀 Production Checklist

- [ ] Domain properly configured with DNS
- [ ] SSL certificate automatically generated
- [ ] Environment variables securely set
- [ ] Health checks passing
- [ ] Logs accessible and monitored
- [ ] Webhook configured for auto-deployment
- [ ] Rate limits appropriate for usage
- [ ] Backup strategy for persistent data
- [ ] Resource limits configured
- [ ] Security headers enabled

Your Instagram Scraper API is now ready for production on Dokploy! 🎉 