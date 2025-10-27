#!/bin/bash
# Utility script to rebuild the LabNote RAG Redis index on demand, e.g. from a maintenance pod.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${SCRIPT_DIR}/labnote-ai-backend"

if [ ! -d "${APP_DIR}" ]; then
    echo "Unable to locate labnote-ai-backend directory at ${APP_DIR}" >&2
    exit 1
fi

export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
export EMBEDDING_MODEL="${EMBEDDING_MODEL:-nomic-embed-text}"

exec /opt/venv/bin/python "${APP_DIR}/scripts/rebuild_rag_index.py" "$@"
