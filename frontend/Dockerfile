# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build production application
RUN npm run build

# Production stage with Nginx
FROM nginx:alpine

# Install OpenSSL for htpasswd creation
RUN apk add --no-cache openssl

# Copy nginx configuration
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY nginx/create-htpasswd.sh /docker-entrypoint.d/40-create-htpasswd.sh
COPY nginx/setup-env.sh /docker-entrypoint.d/30-setup-env.sh

# Make the scripts executable
RUN chmod +x /docker-entrypoint.d/40-create-htpasswd.sh
RUN chmod +x /docker-entrypoint.d/30-setup-env.sh

# Copy built application from the build stage
COPY --from=build /app/build /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Nginx will start automatically when the container starts
# The entrypoint script will run create-htpasswd.sh before nginx starts