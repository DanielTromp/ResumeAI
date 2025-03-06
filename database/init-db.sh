#!/bin/bash
# Initialize PostgreSQL database for ResumeAI

echo "🔄 Setting up PostgreSQL database for ResumeAI..."

# Set environment variables if not running in Docker (adjust as needed)
if [ -z "$PG_HOST" ]; then
  export PG_HOST="localhost"
fi
if [ -z "$PG_PORT" ]; then
  export PG_PORT="5432"
fi
if [ -z "$PG_USER" ]; then
  export PG_USER="postgres"
fi
if [ -z "$PG_PASSWORD" ]; then
  export PG_PASSWORD="postgres"
fi
if [ -z "$PG_DATABASE" ]; then
  export PG_DATABASE="resumeai"
fi

# Check if psql is installed
if ! command -v psql &> /dev/null; then
  echo "❌ Error: PostgreSQL client (psql) is not installed."
  exit 1
fi

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until PGPASSWORD=$PG_PASSWORD psql -h $PG_HOST -p $PG_PORT -U $PG_USER -c '\q'; do
  echo "PostgreSQL is unavailable - waiting..."
  sleep 1
done

echo "✅ PostgreSQL is up and running."

# Create database if it doesn't exist
PGPASSWORD=$PG_PASSWORD psql -h $PG_HOST -p $PG_PORT -U $PG_USER -tc "SELECT 1 FROM pg_database WHERE datname = '$PG_DATABASE'" | grep -q 1 || \
PGPASSWORD=$PG_PASSWORD psql -h $PG_HOST -p $PG_PORT -U $PG_USER -c "CREATE DATABASE $PG_DATABASE"

# Load init SQL scripts
echo "📄 Loading SQL initialization scripts..."
for sql_file in $(find "$(dirname "$0")/init" -name "*.sql" | sort); do
  echo "Loading $sql_file..."
  PGPASSWORD=$PG_PASSWORD psql -h $PG_HOST -p $PG_PORT -U $PG_USER -d $PG_DATABASE -f "$sql_file"
done

echo "🚀 Database initialization complete!"

# Run the import script if available
if [ -f "../backend/app/import_resumes_to_postgres.py" ]; then
  echo "🔄 Do you want to import resumes to PostgreSQL? (y/n)"
  read -r import_choice
  if [ "$import_choice" = "y" ]; then
    echo "🔄 Starting resume import to PostgreSQL..."
    cd ../backend && python -m app.import_resumes_to_postgres --clear
  fi
fi

echo "✅ Setup complete!"