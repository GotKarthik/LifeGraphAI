#!/bin/bash

# Exit on error for the initial setup
set -e

echo "🚀 Starting LifeGraphAI..."

# 1. Start Docker Infrastructure (Postgres, Redis, MinIO)
echo "📦 Starting Docker containers..."
docker-compose up -d

# Function to clean up background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down LifeGraphAI services..."
    kill $API_PID 2>/dev/null || true
    kill $CELERY_PID 2>/dev/null || true
    kill $WEB_PID 2>/dev/null || true
    echo "✅ Shutdown complete."
    exit
}

# Trap SIGINT (Ctrl+C) and call cleanup
trap cleanup SIGINT SIGTERM

# 2. Start FastAPI Backend
echo "⚙️  Starting FastAPI Backend on port 8000..."
cd apps/api
source venv/bin/activate
uvicorn main:app --reload --port 8000 &
API_PID=$!
cd ../..

# 3. Start Celery Worker
echo "👷 Starting Celery Worker..."
cd apps/api
source venv/bin/activate
OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES celery -A core.celery_app worker --pool=solo -Q celery,main-queue --loglevel=info &
CELERY_PID=$!
cd ../..

# 4. Start Next.js Frontend
echo "🌐 Starting Next.js Frontend on port 3000..."
cd apps/web
npm run dev &
WEB_PID=$!
cd ../..

echo "--------------------------------------------------------"
echo "✅ All services started! Press Ctrl+C to stop everything."
echo "🌍 Frontend: http://localhost:3000"
echo "🛠️  Backend API: http://localhost:8000/docs"
echo "--------------------------------------------------------"

# Keep the script running and wait for background processes
wait
