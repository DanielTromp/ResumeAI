# Frontend-Backend Integration Guide for Raspberry Pi

This guide explains how to run ResumeAI on a Raspberry Pi by integrating the React frontend with the FastAPI backend to prevent network connectivity issues.

## The Problem

When running in Docker on a Raspberry Pi, the frontend container often has trouble connecting to the backend container. This results in errors like:

- "Failed to load dashboard data"
- "Network Error" in the console
- "host not found in upstream 'backend'"

## The Solution

Instead of running separate containers for frontend and backend, we'll serve the React frontend directly from the FastAPI backend. This eliminates all network connectivity issues.

## How It Works

1. The React frontend is built as a static site
2. The built files are copied to the backend's frontend directory
3. FastAPI serves these static files alongside the API
4. All requests use relative paths (/api/...)

## Setup Instructions

### Option 1: Using the Setup Script (Recommended)

1. Run the setup script:
   ```
   ./setup-integrated-frontend.sh
   ```

2. Restart the application:
   ```
   ./manage.sh docker-down
   ./manage.sh docker-up
   ```

3. Access the application:
   ```
   http://localhost:8008
   ```

### Option 2: Manual Setup

1. Build the frontend:
   ```
   cd frontend
   npm install
   npm run build
   cd ..
   ```

2. Create the frontend directory in the backend:
   ```
   sudo mkdir -p backend/frontend
   sudo cp -r frontend/build/* backend/frontend/
   sudo chown -R $USER backend/frontend
   ```

3. Update docker-compose.yml to mount the frontend build:
   ```
   volumes:
     - ./frontend/build:/app/frontend
   ```

4. Comment out the frontend service in docker-compose.yml

5. Restart the application:
   ```
   ./manage.sh docker-down
   ./manage.sh docker-up
   ```

## Troubleshooting

### "Permission denied" copying files

If you get "Permission denied" when copying files, use sudo:
```
sudo mkdir -p backend/frontend
sudo cp -r frontend/build/* backend/frontend/
sudo chown -R $USER backend/frontend
```

### "React build directory not found"

This means FastAPI can't find the frontend files. Check:
1. Did the React build complete successfully?
2. Are the files in backend/frontend?
3. Is the volume mount correct in docker-compose.yml?

### Still having network issues

If you're still having DNS resolution issues:
1. Add an entry to your /etc/hosts file:
   ```
   127.0.0.1 backend
   ```
2. Try running with host network mode in docker-compose.yml:
   ```
   network_mode: host
   ```

## Reverting to Separate Containers

To go back to separate frontend and backend containers:

1. Uncomment the frontend service in docker-compose.yml
2. Remove the frontend volume mount from the backend service
3. Restart the services:
   ```
   ./manage.sh docker-down
   ./manage.sh docker-up
   ```