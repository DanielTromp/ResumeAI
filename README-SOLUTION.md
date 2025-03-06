# ResumeAI Development Setup

This document provides instructions for setting up the ResumeAI development environment, addressing network connectivity issues between Docker containers.

## Simplified Development Approach

Due to networking issues between frontend and backend Docker containers, we recommend a hybrid approach:

1. Run the backend in Docker (for isolation and dependencies)
2. Run the frontend directly on your host machine (for better network connectivity)

## Setup Instructions

### Step 1: Start the Backend Container

```bash
# Start only the backend services
docker compose -f docker-compose.simple.yml up -d
```

This will start the backend API on http://localhost:8008

### Step 2: Run the Frontend Directly

```bash
# Execute the frontend setup script
./setup-frontend.sh
```

This script will:
1. Change to the frontend directory
2. Update the proxy configuration to point to http://localhost:8008
3. Start the React development server

The frontend will be available at http://localhost:3000 and will communicate with the backend at http://localhost:8008.

## Why This Approach?

Docker networking between containers can be complex and varies across different host operating systems. Running the frontend directly on the host machine eliminates these networking issues while still providing a good development experience with:

- Hot module reloading for the frontend
- Clean containerization for the backend
- Consistent access to the backend API

## Backup and Restore

The backup and restore scripts still work with this hybrid setup:

```bash
# Create a backup
./backup.sh

# Restore from a backup
./restore.sh ./backups/resumeai_backup_YYYYMMDD_HHMMSS.tar.gz
```

## Production Deployment

For production, you can still use the full Docker Compose setup with both frontend and backend containers, as networking issues are typically more predictable in production environments.