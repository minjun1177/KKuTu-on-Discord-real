#!/usr/bin/env bash
set -euo pipefail

PIDS=$(pgrep -f "python( -u)? app\.py" || true)

if [ -z "${PIDS}" ]; then
  echo "No running bot processes found."
  exit 0
fi

echo "Stopping bot processes: ${PIDS}"
kill ${PIDS} || true

sleep 1
REMAINING=$(pgrep -f "python( -u)? app\.py" || true)

if [ -n "${REMAINING}" ]; then
  echo "Force stopping remaining processes: ${REMAINING}"
  kill -9 ${REMAINING} || true
fi

echo "Bot processes stopped."