#!/bin/bash
# API Check Script for ResumeAI
# This script checks if the backend API is accessible

echo "=== ResumeAI API Check ==="
echo "Testing backend API connection..."

# Check if curl is installed
if ! command -v curl &> /dev/null; then
    echo "curl is not installed. Please install it with:"
    echo "  sudo apt install curl"
    exit 1
fi

# Check backend status
echo "Testing backend API at http://localhost:8008/api/statistics/vacancies..."
RESPONSE=$(curl -s -I -o /dev/null -w "%{http_code}" http://localhost:8008/api/statistics/vacancies)

if [ "$RESPONSE" = "200" ]; then
    echo "✅ Backend API is accessible"
else
    echo "❌ Backend API returned status code: $RESPONSE"
    echo "Trying an alternative address..."
    
    # Try the Docker service name
    RESPONSE=$(curl -s -I -o /dev/null -w "%{http_code}" http://backend:8008/api/statistics/vacancies)
    
    if [ "$RESPONSE" = "200" ]; then
        echo "✅ Backend API is accessible via 'backend:8008'"
        echo "The issue might be in the frontend configuration. Set REACT_APP_BACKEND_URL=http://backend:8008"
    else
        echo "❌ Backend API is not accessible via 'backend:8008' either"
        echo "Checking if backend service is running..."
        
        BACKEND_RUNNING=$(docker ps --filter name=resumeai_backend -q)
        if [ -z "$BACKEND_RUNNING" ]; then
            echo "❌ Backend container is not running"
            echo "Try restarting the services with: ./manage.sh docker-up"
        else
            echo "✅ Backend container is running"
            echo "Checking backend logs for errors..."
            docker logs resumeai-backend-1 --tail 20
        fi
    fi
fi

echo
echo "Testing frontend connection to backend..."
echo "Opening the frontend in browser will show more detailed connection logs in the browser console."
echo
echo "For Raspberry Pi, try this fix:"
echo "1. Edit docker-compose.yml and uncomment the frontend service with host network mode"
echo "2. Add REACT_APP_BACKEND_URL=http://localhost:8008 to the environment variables"
echo "3. Restart the services with: ./manage.sh docker-down && ./manage.sh docker-up"
echo
echo "=== End of API Check ==="