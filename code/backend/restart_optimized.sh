#!/bin/bash
# Restart script for RoadWatch application with memory optimizations

echo "🔄 Restarting RoadWatch with memory optimizations..."

# Stop current services
echo "⏹️  Stopping current services..."
pkill -f gunicorn || echo "No gunicorn processes found"

# Clear any potential memory caches
echo "🧹 Clearing system caches..."
sync

# Navigate to backend directory
cd /home/rishi/roadwatch/code/backend

# Activate virtual environment
source .venv/bin/activate

# Collect static files (if needed)
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Check database integrity
echo "🔍 Checking database integrity..."
python manage.py check

# Start Gunicorn with new memory-optimized configuration
echo "🚀 Starting Gunicorn with optimized configuration..."
if [ "$EUID" -eq 0 ]; then
    # Running as root
    gunicorn -c gunicorn/gunicorn.conf.py pothole_tracker.wsgi:application &
else
    # Need sudo for port 85
    sudo $(which gunicorn) -c gunicorn/gunicorn.conf.py pothole_tracker.wsgi:application &
fi

# Wait a moment for startup
sleep 5

# Check if service started successfully
if pgrep -f gunicorn > /dev/null; then
    echo "✅ Gunicorn started successfully"
    echo "📊 Current memory usage:"
    ps aux | grep gunicorn | grep -v grep | head -5
    echo ""
    echo "🌐 Website should be accessible at: http://10.10.0.173:85"
else
    echo "❌ Failed to start Gunicorn"
    echo "Check logs: tail -f logs/gunicorn_roadwatch_error.log"
    exit 1
fi

echo "🎉 RoadWatch restart completed!"
echo "💡 Monitor memory usage with: ./monitor_memory.sh"
echo "🔧 If JavaScript errors occur, run the base64 conversion: python manage.py convert_base64_to_files"
