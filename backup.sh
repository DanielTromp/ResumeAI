#!/bin/bash

# ResumeAI Backup Script
# This script creates a full backup of the application, including code and data

# Configuration
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/resumeai_backup_$DATE.tar.gz"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if docker-compose is running
if [ "$(docker ps | grep resumeai_backup)" ]; then
  echo "Using Docker backup service..."
  # Just trigger the backup service to do its job
  docker compose exec backup /bin/sh -c 'DATE=$(date +%Y%m%d_%H%M%S); tar -czf /backups/resumeai_backup_$DATE.tar.gz /backup'
  echo "Backup completed by Docker service!"
else
  echo "Creating manual backup..."
  
  # Create temporary directory
  TEMP_DIR=$(mktemp -d)
  
  # Copy code directories
  echo "Copying code directories..."
  cp -r ./backend "$TEMP_DIR/"
  cp -r ./frontend "$TEMP_DIR/"
  
  # Export Docker volumes (if Docker is running)
  if [ "$(docker ps | grep resumeai)" ]; then
    echo "Exporting Docker volumes..."
    # Create directories for volume data
    mkdir -p "$TEMP_DIR/volumes/backend_data"
    mkdir -p "$TEMP_DIR/volumes/resume_storage"
    
    # Export volume data using Docker
    docker run --rm -v resumeai_backend_data:/data -v "$TEMP_DIR/volumes/backend_data:/backup" alpine tar -cf /backup/data.tar -C /data .
    docker run --rm -v resumeai_resume_storage:/data -v "$TEMP_DIR/volumes/resume_storage:/backup" alpine tar -cf /backup/data.tar -C /data .
  fi
  
  # Create backup archive
  echo "Creating backup archive..."
  tar -czf "$BACKUP_FILE" -C "$TEMP_DIR" .
  
  # Clean up temporary directory
  rm -rf "$TEMP_DIR"
  
  echo "Backup created: $BACKUP_FILE"
fi

echo "Done!"