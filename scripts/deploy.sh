#!/bin/bash
# ==============================================================================
# Deployment Script for Youth Affairs Bot
# ==============================================================================

set -e

APP_DIR="/opt/youth-bot"
SERVICE_NAME="youth-affairs-bot"

echo "=== Deploying Youth Affairs Bot ==="

cd "${APP_DIR}"

echo "1. Pulling latest changes from git..."
git pull origin main

echo "2. Installing / updating Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "3. Running database migrations..."
alembic upgrade head

echo "4. Restarting systemd service..."
sudo systemctl restart "${SERVICE_NAME}"

echo "5. Checking service status..."
sudo systemctl status "${SERVICE_NAME}" --no-pager

echo "=== Deployment finished successfully! ==="
