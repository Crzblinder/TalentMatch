#!/bin/bash
set -e

echo "Starting TalentMatch Engine locally..."

# Backend
if [ ! -d "backend/.venv" ]; then
  echo "Creating backend virtual environment..."
  python3 -m venv backend/.venv
fi
source backend/.venv/bin/activate
pip install -q -r backend/requirements.txt

cd backend
python scripts/init_db.py
python scripts/seed_data.py
cd ..

# Frontend
cd frontend
npm install
cd ..

# Start backend in background
source backend/.venv/bin/activate
uvicorn backend.app.main:app --reload --port 8000 &
BACKEND_PID=$!

# Start frontend in background
cd frontend
npm run dev &
FRONTEND_PID=$!

cd ..
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo "Open http://localhost:5173"

wait
