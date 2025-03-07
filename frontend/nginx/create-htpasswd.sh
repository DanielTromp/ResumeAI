#!/bin/sh
# Script to create .htpasswd file

# Get environment variables or use defaults
USERNAME=${AUTH_USERNAME:-admin}
PASSWORD=${AUTH_PASSWORD:-resumeai}

# Create the .htpasswd file
echo "Creating .htpasswd file with username: $USERNAME"
printf "$USERNAME:$(openssl passwd -apr1 $PASSWORD)\n" > /etc/nginx/.htpasswd

# Set permissions
chmod 644 /etc/nginx/.htpasswd

# Print confirmation
echo "Basic auth credentials created successfully"