#!/bin/bash

# Complete production setup script for Viral Together FastAPI

set -e

PROJECT_DIR="/c/Users/user/projects/viral-together"
SERVICE_NAME="viral-together"
DOMAIN="http://195.201.27.127"

echo "🚀 Setting up Viral Together FastAPI for production..."

# Update system
sudo apt update

# Install required packages
sudo apt install -y nginx postgresql postgresql-contrib python3-pip python3-venv

# Create project directory and set permissions
sudo mkdir -p $PROJECT_DIR/logs
sudo chown -R www-data:www-data $PROJECT_DIR
sudo chmod -R 755 $PROJECT_DIR

# Install Gunicorn
cd $PROJECT_DIR
source viralt/bin/activate
pip install gunicorn

# Copy systemd service file
sudo cp $PROJECT_DIR/viral-together.service /etc/systemd/system/

# Copy nginx configuration
sudo cp $PROJECT_DIR/viral-together /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/viral-together /etc/nginx/sites-enabled/

# Remove default nginx site
sudo rm -f /etc/nginx/sites-enabled/default

# Copy logrotate configuration
sudo cp $PROJECT_DIR/viral-together /etc/logrotate.d/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

# Test nginx configuration
sudo nginx -t

# Start and enable nginx
sudo systemctl enable nginx
sudo systemctl start nginx

# Setup SSL with Let's Encrypt (optional)
read -p "Do you want to setup SSL with Let's Encrypt? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo apt install -y certbot python3-certbot-nginx
    sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN
fi

# Setup firewall
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw --force enable

echo "✅ Setup complete!"
echo ""
echo "�� Service Management Commands:"
echo "  Status: sudo systemctl status $SERVICE_NAME"
echo "  Logs: sudo journalctl -u $SERVICE_NAME -f"
echo "  Restart: sudo systemctl restart $SERVICE_NAME"
echo ""
echo "🌐 Nginx Management Commands:"
echo "  Status: sudo systemctl status nginx"
echo "  Logs: sudo tail -f /var/log/nginx/viral-together.access.log"
echo "  Test: sudo nginx -t"
echo "  Reload: sudo systemctl reload nginx"
echo ""
echo "🔍 Health Check:"
echo "  HTTP: curl http://$DOMAIN/health"
echo "  HTTPS: curl https://$DOMAIN/health"
echo ""
echo "📊 Monitoring:"
echo "  App logs: tail -f $PROJECT_DIR/logs/access.log"
echo "  Error logs: tail -f $PROJECT_DIR/logs/error.log"