#!/bin/bash
# Start Celery Worker for Batch Audio Processing
# This script starts the Celery worker with appropriate configuration

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env.local" ]; then
    export $(cat "$PROJECT_ROOT/.env.local" | grep -v '^#' | xargs)
fi

# Set Redis configuration
export REDIS_HOST=${REDIS_HOST:-localhost}
export REDIS_PORT=${REDIS_PORT:-6380}
export REDIS_DB=${REDIS_DB:-0}

# Set STT service configuration
export STT_SERVICE_HOST=${STT_SERVICE_HOST:-localhost}
export STT_SERVICE_PORT=${STT_SERVICE_PORT:-50054}

echo "========================================="
echo "Starting Celery Worker for Batch Audio Processing"
echo "========================================="
echo "Redis: ${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB}"
echo "STT Service: ${STT_SERVICE_HOST}:${STT_SERVICE_PORT}"
echo "Workers: 4 (concurrent)"
echo "========================================="

# Activate virtual environment if it exists
if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# Change to project root
cd "$PROJECT_ROOT"

# Start Celery worker
celery -A src.core.batch_processor.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --pool=prefork \
    --max-tasks-per-child=50 \
    --time-limit=3600 \
    --soft-time-limit=3300 \
    --queues=audio_processing \
    --hostname=audio-worker@%h

# Note: Use Ctrl+C to stop the worker gracefully
