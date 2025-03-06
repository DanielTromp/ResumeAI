#!/bin/bash

echo "Checking backend API..."
curl -s http://localhost:8008/ | grep -o "ResumeAI"

echo "Checking frontend container directly..."
curl -s http://localhost:3000 | head -5

echo "Containers status:"
docker ps

echo "Network inspection:"
docker network inspect resumeai_default | grep -A 10 "Containers"