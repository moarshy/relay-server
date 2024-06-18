#!/bin/bash

# Define the project directory
PROJECT_DIR=$(pwd)

# Install dependencies using Poetry
poetry install --no-root

# Activate the Poetry-created virtual environment
POETRY_VENV_PATH=$(poetry env info -p)

# Create the systemd service file
SERVICE_FILE="/etc/systemd/system/fastapi_relay.service"
echo "[Unit]
Description=FastAPI Relay Server
After=network.target

[Service]
User=$(whoami)
Group=$(whoami)
WorkingDirectory=$PROJECT_DIR
ExecStart=$POETRY_VENV_PATH/bin/uvicorn relay_server:app --host 0.0.0.0 --port 8765 --ws-ping-interval 600 --ws-ping-timeout 600
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target" | sudo tee $SERVICE_FILE

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable and start the service
sudo systemctl enable fastapi_relay.service
sudo systemctl start fastapi_relay.service

echo "Service launched successfully!"
