#!/usr/bin/env bash
set -euo pipefail

PIDS=$(pgrep -f "python( -u)? app\.py" || true)
if [ -n "${PIDS}" ]; then
	echo "Bot is already running: ${PIDS}"
	exit 1
fi

python -u app.py > bot.log 2>&1 &
echo "Bot started with PID: $!"