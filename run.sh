#!/bin/bash
set -e

uv run narra-tron serve --host 127.0.0.1 --port 8000 &

sleep 2

set -a && source .env && set +a && python pi/camera.py
