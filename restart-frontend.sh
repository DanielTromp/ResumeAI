#!/bin/bash

# Stop any existing frontend processes
pkill -f "react-scripts start" || true
sleep 2

# Change to frontend directory
cd frontend

# Install required packages
npm install

# Start the frontend server
echo "Starting frontend server..."
npm start