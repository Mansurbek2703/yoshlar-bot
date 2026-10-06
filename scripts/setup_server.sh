#!/usr/bin/env bash
set -e

echo "=== 1. Setting up PostgreSQL ==="
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='youth_user'" | grep -q 1 || \
sudo -u postgres psql -c "CREATE USER youth_user WITH PASSWORD 'youth_secure_password_2026!';"

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='youth_bot'" | grep -q 1 || \
sudo -u postgres psql -c "CREATE DATABASE youth_bot OWNER youth_user;"

sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE youth_bot TO youth_user;"
echo "PostgreSQL setup complete."

echo "=== 2. Creating directory /opt/youth-bot ==="
mkdir -p /opt/youth-bot
chown -R boss:boss /opt/youth-bot

echo "=== 3. Cloning repository ==="
if [ ! -d /opt/youth-bot/.git ]; then
    git clone https://github.com/Mansurbek2703/yoshlar-bot.git /opt/youth-bot
else
    cd /opt/youth-bot && git pull origin main
fi
chown -R boss:boss /opt/youth-bot

echo "=== 4. Setting up Python environment ==="
cd /opt/youth-bot
if [ ! -d venv ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "=== 5. Writing production .env ==="
cat << 'EOF' > /opt/youth-bot/.env
# Telegram Bot Configuration
BOT_TOKEN=8830551287:AAFVlYoFLTLlbyUcuOrFWU3Nq8D5SCTfnak

# Database Configuration (PostgreSQL 14)
DATABASE_URL=postgresql+asyncpg://youth_user:youth_secure_password_2026!@localhost:5432/youth_bot

# Administrator Telegram IDs
ADMIN_IDS=123456789

# Webhook Configuration (via Nginx reverse proxy https://yoshlar.akhu.uz)
USE_WEBHOOK=True
WEBHOOK_HOST=https://yoshlar.akhu.uz
WEBHOOK_PATH=/webhook
WEBHOOK_SECRET=akhu_yoshlar_webhook_secret_2026
WEB_SERVER_HOST=0.0.0.0
WEB_SERVER_PORT=8000

# File limits (50 MB)
MAX_FILE_SIZE=52428800

# System Settings
TIMEZONE=Asia/Tashkent
LOG_LEVEL=INFO
EOF
chown boss:boss /opt/youth-bot/.env

echo "=== 6. Running database migrations ==="
alembic upgrade head

echo "=== 7. Configuring and starting systemd service ==="
cp /opt/youth-bot/systemd/youth-affairs-bot.service /etc/systemd/system/youth-affairs-bot.service
systemctl daemon-reload
systemctl enable youth-affairs-bot
systemctl restart youth-affairs-bot

echo "=== 8. Checking service status ==="
systemctl status youth-affairs-bot --no-pager

echo "=== ALL STEPS COMPLETED ==="
