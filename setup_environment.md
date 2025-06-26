# Environment Setup Instructions

## Prerequisites

1. **Python 3.8+** - Make sure you have Python installed
2. **Redis Server** - Required for rate limiting (optional but recommended)
3. **OpenAI API Key** - Required for content parsing

## Step 1: Clone and Setup Project

```bash
# Clone the repository (if not already done)
cd instagram-scraper

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Environment Configuration

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file and configure the following:**

### Required Configuration

- **OPENAI_API_KEY**: Get your API key from [OpenAI](https://platform.openai.com/api-keys)
  ```
  OPENAI_API_KEY=sk-your-actual-api-key-here
  ```

### Optional Configuration

- **FLASK_ENV**: Set to `development` for local development or `production` for production
- **SECRET_KEY**: Change this to a secure random string for production
- **REDIS_URL**: Redis connection string for rate limiting
- **Rate Limits**: Adjust according to your needs
- **Timeouts**: Configure scraping and OpenAI timeouts
- **Logging**: Set log level and format

## Step 3: Redis Setup (For Rate Limiting)

### Option A: Using Docker (Recommended)
```bash
# Run Redis in Docker
docker run -d -p 6379:6379 --name redis redis:alpine

# Verify Redis is running
docker ps
```

### Option B: Install Redis Locally

**macOS (using Homebrew):**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**Windows:**
- Download Redis from [Redis Windows](https://github.com/microsoftarchive/redis/releases)
- Or use WSL with Ubuntu instructions

### Option C: Skip Redis (Not Recommended)
If you don't want to use Redis, the app will fall back to in-memory storage, but rate limiting won't work across server restarts.

## Step 4: Verify Installation

1. **Test Redis connection (if using Redis):**
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

2. **Test OpenAI API key:**
   ```bash
   python -c "from openai import OpenAI; client = OpenAI(); print('OpenAI API key is valid')"
   ```

## Step 5: Run the Application

```bash
# Start the Flask application
python app.py
```

The API will be available at: `http://localhost:5000`

## Step 6: Test the API

```bash
# Test health endpoint
curl http://localhost:5000/health

# Test scraping endpoint (replace with a real Instagram URL)
curl -X POST http://localhost:5000/scrape \
  -H "Content-Type: application/json" \
  -d '{"instagram_url": "https://www.instagram.com/p/XXXXXXXXX/"}'
```

## Production Deployment

### Environment Variables for Production

```bash
# Set production environment
FLASK_ENV=production

# Use a strong secret key
SECRET_KEY=your-very-secure-secret-key-here

# Use Redis for production
REDIS_URL=redis://your-redis-server:6379/0

# Adjust rate limits for production load
DEFAULT_RATE_LIMIT=100 per hour
SCRAPE_RATE_LIMIT=20 per hour

# Set appropriate timeouts
SCRAPE_TIMEOUT=120
OPENAI_TIMEOUT=60

# Set logging level
LOG_LEVEL=WARNING
```

### Using Gunicorn for Production

```bash
# Install gunicorn (already in requirements.txt)
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Troubleshooting

### Common Issues

1. **"Missing required environment variables: OPENAI_API_KEY"**
   - Make sure your `.env` file contains a valid OpenAI API key
   - Verify the key is correct and has billing enabled

2. **Redis connection errors**
   - Make sure Redis is running: `redis-cli ping`
   - Check the REDIS_URL in your `.env` file
   - For Docker: `docker ps` to see if Redis container is running

3. **Instagram scraping fails**
   - Instagram may block requests from certain IPs
   - Try different post URLs (public posts work better)
   - Check if the post exists and is public

4. **Rate limiting not working**
   - Ensure Redis is running and accessible
   - Check Redis connection with `redis-cli ping`
   - Verify REDIS_URL in `.env` file

5. **OpenAI parsing fails**
   - Verify API key is valid and has sufficient credits
   - Check OpenAI service status
   - Reduce content size if hitting token limits

### Getting Help

- Check the logs in `instagram_scraper.log`
- Enable debug logging by setting `LOG_LEVEL=DEBUG`
- Test individual components using the test suite

## Security Notes

- **Never commit your `.env` file** - it contains sensitive API keys
- **Change the SECRET_KEY** for production deployments
- **Use HTTPS** in production
- **Monitor API usage** to avoid unexpected costs
- **Set appropriate rate limits** to prevent abuse 