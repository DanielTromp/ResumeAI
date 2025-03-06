#!/bin/bash

# ResumeAI Restore Script
# This script restores a backup of the application

# Check if backup file is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file $BACKUP_FILE not found"
    exit 1
fi

echo "Restoring from backup: $BACKUP_FILE"

# Create temporary directory
TEMP_DIR=$(mktemp -d)

# Extract backup archive
echo "Extracting backup archive..."
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# Check if current installation exists and confirm overwrite
if [ -d "./backend" ] || [ -d "./frontend" ]; then
    read -p "This will overwrite your current installation. Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Restore cancelled"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
fi

# Stop running services if they exist
if [ "$(docker ps | grep resumeai)" ]; then
    echo "Stopping running containers..."
    docker compose down
fi

# Restore code directories
echo "Restoring code directories..."
if [ -d "$TEMP_DIR/backend" ]; then
    rm -rf ./backend
    cp -r "$TEMP_DIR/backend" ./
fi

if [ -d "$TEMP_DIR/frontend" ]; then
    rm -rf ./frontend
    cp -r "$TEMP_DIR/frontend" ./
fi

# Restore Docker volumes (if they exist in backup)
if [ -d "$TEMP_DIR/volumes" ]; then
    echo "Restoring Docker volumes..."
    
    # Create volumes if they don't exist
    docker volume create resumeai_backend_data
    docker volume create resumeai_resume_storage
    
    # Restore volume data
    if [ -f "$TEMP_DIR/volumes/backend_data/data.tar" ]; then
        docker run --rm -v resumeai_backend_data:/data -v "$TEMP_DIR/volumes/backend_data:/backup" alpine /bin/sh -c "cd /data && tar -xf /backup/data.tar"
    fi
    
    if [ -f "$TEMP_DIR/volumes/resume_storage/data.tar" ]; then
        docker run --rm -v resumeai_resume_storage:/data -v "$TEMP_DIR/volumes/resume_storage:/backup" alpine /bin/sh -c "cd /data && tar -xf /backup/data.tar"
    fi
fi

# Clean up temporary directory
rm -rf "$TEMP_DIR"

echo "Restore completed!"
echo "You can now start the application using: docker compose up -d"