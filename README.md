# LeetCode Recommender Django App

## Overview
A Django app where users enter a LeetCode username and select a goal (switch prep/interview prep/practice) to:
- Fetch recent solved problems from LeetCode
- Analyze difficulty distribution and topic frequency
- Get AI-powered problem recommendations via Google Gemini

## Prerequisites
- Python 3.9+
- pip
- Google Gemini API key (free tier available at [ai.google.dev](https://ai.google.dev))

## Local Development Setup

### 1. Clone and Navigate
```bash
git clone <your-repo-url>
cd new\ project
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```bash
cp .env
```

Edit `.env` and add your Google Gemini API key:
```
AI_PROVIDER=gemini
GOOGLE_API_KEY=your_google_gemini_api_key_here
SECRET_KEY=your_django_secret_key_here
DEBUG=True
```

> **Note**: Generate a strong `SECRET_KEY` using: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`

### 5. Run Migrations
```bash
python manage.py migrate
```

### 6. Start Development Server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.

## Production Deployment

### Environment Configuration
Before deploying, ensure your `.env` file includes:
- `DEBUG=False`
- `SECRET_KEY` (strong, random value)
- `ALLOWED_HOSTS` (your domain(s), comma-separated)
- `GOOGLE_API_KEY` (Gemini API key)

### Using Docker (Recommended)
```bash
docker-compose up -d
```

### Manual Deployment
```bash
pip install gunicorn
gunicorn leetcode_recommender.wsgi:application --bind 0.0.0.0:8000
```

### Database
- **Development**: SQLite (default)
- **Production**: PostgreSQL (recommended)

Set `DATABASE_URL` in `.env` for PostgreSQL:
```
DATABASE_URL=postgresql://user:password@localhost:5432/leetcode_db
```

### Static Files
```bash
python manage.py collectstatic --no-input
```

Serve static files via a reverse proxy (Nginx, Apache) or CDN.

### Caching
- **Development**: Local memory cache
- **Production**: Configure Redis for multi-instance deployments

Add to `.env`:
```
CACHE_URL=redis://localhost:6379/0
```

## API Integrations

### LeetCode API
- **GraphQL Endpoint**: Fetches recent public submissions
- **REST Endpoint**: Fallback for submission data
- **Problems Endpoint**: Enriches problem metadata (difficulty, topics)

### Google Gemini AI
- Analyzes solved patterns and generates personalized problem recommendations
- Uses free tier (has usage limits; consider upgrading for high-traffic deployments)

## Features
- ✅ Fetch recent LeetCode submissions (public profiles)
- ✅ Analyze problem difficulty and topic distribution
- ✅ AI-powered recommendations tailored to user goals
- ✅ Session-based caching (15 min for submissions, 60 min for problem DB)
- ✅ Error handling and logging

## File Structure
```
leetcode_recommender/
├── core/
│   ├── services/
│   │   ├── leetcode_service.py     # LeetCode API integration
│   │   ├── ai_service.py           # Gemini recommendations
│   ├── templates/core/
│   │   ├── base.html
│   │   └── dashboard.html
│   ├── forms.py                    # User input form
│   ├── views.py                    # Main request handler
│   ├── urls.py
│   ├── models.py
├── leetcode_recommender/
│   ├── settings.py                 # Django configuration
│   ├── urls.py
│   ├── wsgi.py
├── manage.py
├── requirements.txt
├── .env.example
├── Dockerfile
└── README.md
```

## Security Considerations
- Never commit `.env` or `.env.example` with real API keys
- Use strong, unique `SECRET_KEY` for each environment
- Set `DEBUG=False` in production
- Configure `ALLOWED_HOSTS` to your domain(s)
- Use HTTPS in production
- Keep dependencies up-to-date: `pip install --upgrade -r requirements.txt`

## Troubleshooting

### LeetCode API Errors
- **"User not found"**: Check if the LeetCode username is correct and public
- **"No recent public submissions"**: The user's recent submissions may be private

### Gemini API Issues
- **Quota exceeded**: Upgrade your Google AI API plan or wait for rate limits to reset
- **Model not found**: The app automatically falls back to alternative Gemini models

### Database Issues
- Reset migrations: `python manage.py migrate zero core`
- Recreate: `python manage.py migrate`

## Testing
```bash
python manage.py test
```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to GitHub and create a Pull Request

## License
MIT License (or your preferred license)

## Support
For issues, feature requests, or questions, open an issue on GitHub.
