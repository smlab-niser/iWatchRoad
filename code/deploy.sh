#!/bin/bash

# Deploy script for iWatchRoad
# Copies built frontend to staticfiles and restarts services

set -e  # Exit on any error

echo "🚀 Starting deployment..."
echo "📂 Changing directory to /home/rishi/roadwatch/code..."
cd /home/rishi/roadwatch/code

# Copy dist files to staticfiles
echo "📁 Copying frontend build to staticfiles (optionally, remove old files manually)..."
cp -r dist/* ./backend/staticfiles/

# Reload systemd daemon
echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

# Test nginx configuration
echo "🔍 Testing nginx configuration..."
sudo nginx -t

# Reload nginx
echo "🌐 Reloading nginx..."
sudo nginx -s reload

# Restart roadwatch service
echo "🔄 Restarting roadwatch service..."
sudo systemctl restart roadwatch

# Restart nginx
echo "🔄 Restarting nginx..."
sudo systemctl restart nginx

echo "✅ Deployment complete!"
