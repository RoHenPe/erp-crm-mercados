#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR/backend"

export PYTHONPATH="$PROJECT_DIR/backend:${PYTHONPATH:-}"
export ERP_PG_HOST="${ERP_PG_HOST:-192.168.15.109}"
export ERP_PG_PORT="${ERP_PG_PORT:-5432}"
export ERP_PG_USER="${ERP_PG_USER:-rodrigo}"
export ERP_PG_PASS="${ERP_PG_PASS:-rodrigo123}"
export ERP_PG_DB="${ERP_PG_DB:-erp_mercados_db}"
PORT="${PORT:-8090}"

if [ -x "/media/rodrigo/Downloads/ai-agents/.venv/bin/uvicorn" ]; then
    exec /media/rodrigo/Downloads/ai-agents/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
else
    exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
fi
