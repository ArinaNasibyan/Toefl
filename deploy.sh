#!/bin/bash
set -e

echo "=== 🚀 Installing TOEFL Telegram Bot on VPS ==="

# 1. Update system packages
apt-get update -y
apt-get install -y git python3 python3-pip python3-venv ffmpeg

# 2. Clone or update repository
APP_DIR="/opt/toefl-bot"
if [ -d "$APP_DIR" ]; then
    echo "Updating existing repository in $APP_DIR..."
    cd "$APP_DIR"
    git pull origin main
else
    echo "Cloning repository into $APP_DIR..."
    git clone https://github.com/ArinaNasibyan/Toefl.git "$APP_DIR"
    cd "$APP_DIR"
fi

# 3. Create virtual environment and install requirements
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# 4. Create data directory for persistent SQLite database
mkdir -p "$APP_DIR/data"

# 5. Create .env file
cat <<EOF > "$APP_DIR/.env"
BOT_TOKEN=8252283205:AAFx4xhxUE829bvDiaPTKZJzfEG_L3gAaVc
ADMIN_IDS=5423668260
DATABASE_URL=sqlite+aiosqlite:////opt/toefl-bot/data/database.db
DEBUG=false
EOF

# 6. Create systemd service for 24/7 background operation and auto-restart
cat <<EOF > /etc/systemd/system/toefl-bot.service
[Unit]
Description=TOEFL Telegram Bot 24/7 Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/.venv/bin/python -m app.main
Restart=always
RestartSec=5
KillSignal=SIGTERM

[Install]
WantedBy=multi-user.target
EOF

# 7. Reload and start systemd service
systemctl daemon-reload
systemctl enable toefl-bot
systemctl restart toefl-bot

echo "=== ✅ TOEFL Telegram Bot is now running 24/7! ==="
systemctl status toefl-bot --no-pager
