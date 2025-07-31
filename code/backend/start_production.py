"""
Windows-compatible production server startup script using Waitress
"""
import os
import sys
from waitress import serve
from django.core.wsgi import get_wsgi_application

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pothole_tracker.production_settings')

# Initialize Django
import django
django.setup()

if __name__ == "__main__":
    print("🚀 Starting RoadWatch production server with Waitress...")
    print("📡 Server will be available at: http://localhost:8000")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Get the WSGI application
    application = get_wsgi_application()
    
    # Serve with Waitress (Windows-compatible)
    serve(
        application,
        host='0.0.0.0',
        port=8000,
        threads=6,
        connection_limit=1000,
        cleanup_interval=30,
        channel_timeout=120
    )
