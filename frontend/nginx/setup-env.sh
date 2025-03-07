#!/bin/sh
# Script to set up environment variables for Nginx

# Get backend URL from environment or use default
BACKEND_URL=${BACKEND_URL:-http://backend:8008}

# Create Nginx environment file
echo "Creating Nginx environment file"
cat > /etc/nginx/conf.d/environment.conf <<EOF
env BACKEND_URL=$BACKEND_URL;
EOF

echo "Backend URL set to: $BACKEND_URL"