#!/usr/bin/env bash
set -euo pipefail

: "${BOT_TOKEN:?Set BOT_TOKEN before running this script}"
: "${DATABASE_URL:?Set DATABASE_URL before running this script}"

APP_DIR="/opt/toefl-bot"

apt-get update -y
apt-get install -y git python3 python3-pip python3-venv ffmpeg

if [ -d "$APP_DIR/.git" ]; then
    cd "$APP_DIR"
    git pull origin main
else
    git clone https://github.com/ArinaNasibyan/Toefl.git "$APP_DIR"
    cd "$APP_DIR"
fi

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

mkdir -p "$APP_DIR/data"
install -m 600 /dev/null "$APP_DIR/.env"
cat <<EOF > "$APP_DIR/.env"
BOT_TOKEN=$BOT_TOKEN
ADMIN_IDS=${ADMIN_IDS:-}
DATABASE_URL=$DATABASE_URL
DEBUG=${DEBUG:-false}
EOF

cat <<EOF > /etc/systemd/system/toefl-bot.service
[Unit]
Description=TOEFL Telegram Bot
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

systemctl daemon-reload
systemctl enable toefl-bot
systemctl restart toefl-bot
systemctl status toefl-bot --no-pager
