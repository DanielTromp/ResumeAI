#!/bin/bash

# This script sets up the frontend to run outside Docker but connect to Docker backend

# Change to frontend directory
cd frontend

# Update package.json to point proxy to the Docker backend
sed -i '' 's/"proxy": "http:\/\/localhost:8000"/"proxy": "http:\/\/localhost:8008"/' package.json

echo "Starting Frontend in Development Mode..."
echo "Backend API should be running at http://localhost:8008"
echo "Frontend will be available at http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop"

# Start the React development server
npm start