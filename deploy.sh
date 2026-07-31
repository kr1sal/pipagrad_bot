#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

if [[ -n "$(git status --porcelain)" ]]; then
    echo "Working tree has uncommitted changes, aborting." >&2
    git status --short
    exit 1
fi

echo "==> Pulling latest changes"
git fetch origin
git checkout main
git pull --ff-only origin main

echo "==> Rebuilding and restarting bot"
docker compose up -d --build bot

echo "==> Recent logs"
sleep 3
docker compose logs bot --tail=30
