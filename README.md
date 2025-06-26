# Instagram Scraper API

A Flask API endpoint for scraping Instagram posts using Crawl4AI and OpenAI GPT-4o-mini for structured data extraction.

## Features

- 🚀 **Fast Scraping**: Uses Crawl4AI for efficient web scraping
- 🤖 **AI-Powered Parsing**: OpenAI GPT-4o-mini with structured outputs
- 📊 **Comprehensive Data**: Extracts 18+ data points from Instagram posts
- 🛡️ **Robust Validation**: Input validation and error handling
- 🎯 **RESTful API**: Clean JSON API endpoints

## Extracted Data Points

The API extracts the following information from Instagram posts:

- `caption` - Post caption text
- `type` - Post type (image, video, carousel)
- `url` - Original post URL
- `videoUrl` - Video file URL (for videos)
- `imageUrl` - Image file URL
- `displayUrl` - Display image URL
- `shortCode` - Instagram post short code
- `timestamp` - Post creation timestamp
- `likesCount` - Number of likes
- `commentsCount` - Number of comments
- `videoViewCount` - Video view count
- `videoPlayCount` - Video play count
- `ownerUsername` - Account username
- `ownerFullName` - Account full name
- `locationName` - Location tag
- `hashtags` - Array of hashtags
- `mentions` - Array of mentioned users
- `alt` - Alt text for accessibility

## Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd instagram-scraper
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Create .env file
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
```

4. Run the application:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## API Usage

### Health Check
```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "Instagram Scraper API"
}
```

### Scrape Instagram Post
```bash
POST /scrape
Content-Type: application/json

{
  "instagram_url": "https://www.instagram.com/p/XXXXXXXXX/"
}
```

Response:
```json
{
  "success": true,
  "data": {
    "caption": "Amazing sunset! 🌅",
    "type": "image",
    "url": "https://www.instagram.com/p/XXXXXXXXX/",
    "imageUrl": "https://...",
    "shortCode": "XXXXXXXXX",
    "timestamp": "2024-01-15T10:30:00Z",
    "likesCount": 1250,
    "commentsCount": 89,
    "ownerUsername": "photographer",
    "ownerFullName": "Amazing Photographer",
    "hashtags": ["sunset", "photography", "nature"],
    "mentions": ["@friend"],
    "alt": "Beautiful sunset over the ocean"
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": "Invalid Instagram URL. Please provide a valid Instagram post URL."
}
```

## Supported URLs

The API supports various Instagram post formats:
- `https://www.instagram.com/p/XXXXXXXXX/`
- `https://instagram.com/p/XXXXXXXXX/`
- `https://www.instagram.com/reel/XXXXXXXXX/`
- `https://instagram.com/reel/XXXXXXXXX/`
- `https://www.instagram.com/tv/XXXXXXXXX/`

## Configuration

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `FLASK_ENV` | Flask environment | `development` |

## Development

### Project Structure
```
instagram-scraper/
├── app.py              # Main Flask application
├── scraper.py          # Instagram scraper logic
├── models.py           # Pydantic data models
├── config.py           # Configuration management
├── requirements.txt    # Python dependencies
├── UPDATES.md         # Project todos and updates
└── README.md          # This file
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest
```

## Limitations

- Instagram may block requests without proper session handling
- Rate limits apply to both Instagram scraping and OpenAI API
- Some posts may not be accessible due to privacy settings
- Requires valid OpenAI API key with sufficient credits

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is for educational purposes. Please respect Instagram's Terms of Service and robots.txt when scraping.

## Support

If you encounter issues:
1. Check the UPDATES.md file for known issues
2. Ensure your OpenAI API key is valid
3. Verify the Instagram URL format
4. Check the application logs for detailed error messages 