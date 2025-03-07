#!/bin/bash

# Stop any existing backend processes
pkill -f "uvicorn main:app" || true
sleep 2

# Activate virtual environment if available
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Make sure required packages are installed
pip install -r backend/requirements.txt

# Start the backend server
echo "Starting backend server..."
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8008 --reload