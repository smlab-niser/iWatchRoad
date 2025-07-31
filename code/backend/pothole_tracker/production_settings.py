import os
from .settings import *

# Production settings
DEBUG = False

# Allow all hosts for initial deployment (restrict later)
ALLOWED_HOSTS = ['*']

# Security settings (disable SSL redirect for local testing)
SECURE_SSL_REDIRECT = False  # Set to True only when using HTTPS
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Database for production (PostgreSQL recommended)
if 'DATABASE_URL' in os.environ:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(os.environ.get('DATABASE_URL'))
    }
else:
    # Fallback to SQLite for initial deployment
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Email settings for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'admin@potholetracker.com')

# Static files for production
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Additional static files directories
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),  # For the built frontend
]

# Serve React app at root
WHITENOISE_INDEX_FILE = True
WHITENOISE_USE_FINDERS = True

# WhiteNoise middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# CORS for production frontend
CORS_ALLOWED_ORIGINS = [
    "https://your-username.github.io",  # Replace with your actual GitHub Pages URL
    "https://*.github.io",  # Allow any GitHub Pages subdomain
]

# More permissive CORS for development/testing
CORS_ALLOW_ALL_ORIGINS = True  # Only for initial deployment testing
CORS_ALLOW_CREDENTIALS = True

# Additional CORS headers
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Allowed hosts - Allow all for network access
ALLOWED_HOSTS = [
    '*',  # Allow all hosts for local network access
    'localhost',
    '127.0.0.1',
    '.railway.app',  # Railway domains
    '.render.com',   # Render domains
    '.herokuapp.com', # Heroku domains
]

# Secret key from environment
SECRET_KEY = os.environ.get('SECRET_KEY', SECRET_KEY)
