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
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR" --warning=no-unknown-keyword --no-same-owner

# Check if extraction was successful
if [ $? -ne 0 ]; then
    echo "Failed to extract backup archive."
    rm -rf "$TEMP_DIR"
    exit 1
fi

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
fi

# Clean up
echo "Cleaning up..."
rm -rf "$TEMP_DIR"

echo "Restore completed!"
echo "You'll need to manually restore the database and run npm install for the frontend."
echo ""
echo "To restore the database (if using Docker):"
echo "  docker-compose up -d db"
echo "  docker exec resumeai_db psql -U postgres -c \"DROP DATABASE IF EXISTS resumeai;\""
echo "  docker exec resumeai_db psql -U postgres -c \"CREATE DATABASE resumeai;\""
echo "  docker exec -i resumeai_db psql -U postgres -d resumeai < ./database_restore/resumeai.sql"
echo ""
echo "To install frontend dependencies:"
echo "  cd frontend && npm install"