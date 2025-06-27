 # Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies including Chrome for Crawl4AI
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN CHROME_DRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` \
    && wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip \
    && chmod +x /usr/local/bin/chromedriver

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies with verbose output for debugging
RUN pip install --no-cache-dir --upgrade pip

# Install packages one by one to identify any issues
RUN pip install --no-cache-dir --verbose flask==3.0.0
RUN pip install --no-cache-dir --verbose openai==1.52.0
RUN pip install --no-cache-dir --verbose python-dotenv==1.0.0
RUN pip install --no-cache-dir --verbose pydantic==2.10
RUN pip install --no-cache-dir --verbose requests==2.31.0
RUN pip install --no-cache-dir --verbose gunicorn==21.2.0
RUN pip install --no-cache-dir --verbose flask-limiter==3.5.0
RUN pip install --no-cache-dir --verbose redis==5.0.1
RUN pip install --no-cache-dir --verbose pytest==7.4.3
RUN pip install --no-cache-dir --verbose pytest-asyncio==0.21.1
RUN pip install --no-cache-dir --verbose pytest-mock==3.12.0
RUN pip install --no-cache-dir --verbose pytest-cov==4.1.0
RUN pip install --no-cache-dir --verbose python-decouple==3.8

# Install crawl4ai last with specific handling
RUN pip install --no-cache-dir --verbose crawl4ai==0.6.3

# Run crawl4ai setup and install Playwright browsers as root
RUN crawl4ai-setup

# Install Playwright browsers explicitly
RUN playwright install chromium
RUN playwright install-deps

# Copy project files
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app

# Switch to non-root user
USER app

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "--keep-alive", "2", "app:app"] 