#!/bin/bash
# Initialize PostgreSQL database with pgvector for ResumeAI

echo "🔄 Initializing PostgreSQL database for ResumeAI..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
  if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
  elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
  fi
  echo "✅ Virtual environment activated"
fi

# Check if we're running in Docker
if [ -f "/.dockerenv" ]; then
  echo "✅ Running in Docker environment"
  # Use Docker environment variables
  export PG_HOST=${PG_HOST:-db}
else
  echo "ℹ️ Running in local environment"
  # Use local environment variables
  export PG_HOST=${PG_HOST:-localhost}
fi

# Set other default environment variables if not set
export PG_PORT=${PG_PORT:-5432}
export PG_USER=${PG_USER:-postgres}
export PG_PASSWORD=${PG_PASSWORD:-postgres}
export PG_DATABASE=${PG_DATABASE:-resumeai}

echo "ℹ️ Using database: ${PG_HOST}:${PG_PORT}/${PG_DATABASE}"

# Run the initialization script
cd backend
python -m app.db_init --init --test-data --test-search

# Check the exit code
if [ $? -eq 0 ]; then
  echo "✅ Database initialization completed successfully!"
else
  echo "❌ Database initialization failed!"
  exit 1
fi

echo "
You can now start the application with:
  - Backend: cd backend && python main.py
  - Frontend: cd frontend && npm start
"