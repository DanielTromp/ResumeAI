#!/bin/bash
# Simple restore script for Raspberry Pi

# Check if backup file is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    echo "Example: $0 resumeai_backup_20250310_141855.tar.gz"
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file '$BACKUP_FILE' not found"
    echo "Current directory: $(pwd)"
    echo "Files in current directory:"
    ls -l
    exit 1
fi

echo "Creating temporary directory..."
TEMP_DIR=$(mktemp -d)
chmod 755 "$TEMP_DIR"

echo "Extracting backup archive..."
# Try with additional flags on newer systems
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR" --warning=no-unknown-keyword --no-same-owner 2>/dev/null || \
# Fallback to basic extraction on older systems
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR" 2>/dev/null || \
# Last resort, use the simplest form
tar -xf "$BACKUP_FILE" -C "$TEMP_DIR"

# Check if extraction was successful
if [ $? -ne 0 ]; then
    echo "Failed to extract backup archive."
    echo "Trying to extract with verbose output to see the error:"
    tar -xvzf "$BACKUP_FILE" -C "$TEMP_DIR"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# List contents to help with debugging
echo "Extracted backup files:"
find "$TEMP_DIR" -type d -maxdepth 2 | sort

echo "Restoring files..."

# Make sure destination directories exist
mkdir -p backend
mkdir -p frontend
mkdir -p backups
mkdir -p database

# Restore files, skipping node_modules
echo "Restoring backend..."
if [ -d "$TEMP_DIR/backend" ]; then
    cp -r "$TEMP_DIR/backend/"* ./backend/ 2>/dev/null || echo "No backend files found"
fi

echo "Restoring frontend (excluding node_modules)..."
if [ -d "$TEMP_DIR/frontend" ]; then
    # Copy everything except node_modules
    find "$TEMP_DIR/frontend" -mindepth 1 -maxdepth 1 ! -name "node_modules" -exec cp -r {} ./frontend/ \; 2>/dev/null || echo "No frontend files found"
fi

# Restore configuration files
echo "Restoring configuration files..."
if [ -f "$TEMP_DIR/config/.env" ]; then
    cp "$TEMP_DIR/config/.env" ./.env
fi
if [ -f "$TEMP_DIR/config/backend.env" ]; then
    cp "$TEMP_DIR/config/backend.env" ./backend/.env
fi
if [ -f "$TEMP_DIR/config/backend.env.docker" ]; then
    cp "$TEMP_DIR/config/backend.env.docker" ./backend/.env.docker
fi
if [ -f "$TEMP_DIR/config/docker-compose.yml" ]; then
    cp "$TEMP_DIR/config/docker-compose.yml" ./docker-compose.yml
fi

# Restore database dump
echo "Restoring database dump..."
if [ -d "$TEMP_DIR/database_dump" ]; then
    mkdir -p ./database_restore
    cp -r "$TEMP_DIR/database_dump/"* ./database_restore/ 2>/dev/null || echo "No database dump found"
    echo "Database dump files in database_restore:"
    ls -la ./database_restore/
elif [ -f "$TEMP_DIR/database_dump" ]; then
    # In case it's a file instead of a directory
    mkdir -p ./database_restore
    cp "$TEMP_DIR/database_dump" ./database_restore/resumeai.sql
    echo "Database dump saved to database_restore/resumeai.sql"
else
    # Search for SQL files in the temp directory
    echo "Searching for database dump files in backup..."
    find "$TEMP_DIR" -name "*.sql" -type f | while read -r sql_file; do
        echo "Found SQL file: $sql_file"
        mkdir -p ./database_restore
        cp "$sql_file" ./database_restore/resumeai.sql
        echo "Database dump saved to database_restore/resumeai.sql"
        break
    done
fi

# Clean up
echo "Cleaning up..."
rm -rf "$TEMP_DIR"

echo "Restore completed!"
echo "You'll need to manually restore the database and run npm install for the frontend."
echo ""
echo "To restore the database (if using Docker):"
echo "  # First, check your database container name"
echo "  docker ps | grep -i db"
echo ""
echo "  # Start the database if it's not running"
echo "  docker-compose up -d db"
echo ""
echo "  # Use your actual container name (likely resumeai-db-1)"
echo "  docker exec resumeai-db-1 psql -U postgres -c \"DROP DATABASE IF EXISTS resumeai;\""
echo "  docker exec resumeai-db-1 psql -U postgres -c \"CREATE DATABASE resumeai;\""
echo "  docker exec -i resumeai-db-1 psql -U postgres -d resumeai < ./database_restore/resumeai.sql"
echo ""
echo "  # If that doesn't work, try these alternative commands:"
echo "  # docker cp ./database_restore/resumeai.sql resumeai-db-1:/tmp/"
echo "  # docker exec resumeai-db-1 psql -U postgres -d resumeai -f /tmp/resumeai.sql"
echo ""
echo "To install frontend dependencies:"
echo "  cd frontend && npm install"