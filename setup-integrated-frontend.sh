#!/bin/bash
# Setup script for integrated FastAPI/React frontend
# This script builds the React frontend and updates docker-compose.yml

echo "==== ResumeAI Integrated Frontend Setup ===="
echo "This script will build the React frontend and integrate it with the FastAPI backend"

# Check if we're in the correct directory
if [ ! -f "manage.sh" ]; then
    echo "ERROR: This script must be run from the ResumeAI root directory"
    echo "Please cd to the ResumeAI directory and try again"
    exit 1
fi

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo "ERROR: frontend directory not found"
    exit 1
fi

# Build the frontend
echo "Building the frontend..."
cd frontend || exit 1
npm install
npm run build

# Copy the build directory to the backend directory
echo "Copying build files to backend directory..."
mkdir -p ../backend/frontend
cp -r build/* ../backend/frontend/

cd ..

echo "Frontend built successfully!"

# Update docker-compose.yml to use the integrated frontend
echo "Updating docker-compose.yml to use the integrated backend..."

if grep -q "frontend:" docker-compose.yml; then
    # Comment out the frontend service
    sed -i.bak 's/^  frontend:/#  frontend:/g' docker-compose.yml
    sed -i.bak 's/^    build:/#    build:/g' docker-compose.yml
    sed -i.bak 's/^    ports:/#    ports:/g' docker-compose.yml
    sed -i.bak 's/^    environment:/#    environment:/g' docker-compose.yml
    sed -i.bak 's/^    restart:/#    restart:/g' docker-compose.yml
    sed -i.bak 's/^    network_mode:/#    network_mode:/g' docker-compose.yml
    sed -i.bak 's/^    depends_on:/#    depends_on:/g' docker-compose.yml
    sed -i.bak 's/^      - backend/#      - backend/g' docker-compose.yml
    sed -i.bak 's/^    extra_hosts:/#    extra_hosts:/g' docker-compose.yml
    sed -i.bak 's/^      - "host.docker.internal:host-gateway"/#      - "host.docker.internal:host-gateway"/g' docker-compose.yml
    
    echo "docker-compose.yml updated successfully"
else
    echo "WARNING: Could not find frontend service in docker-compose.yml"
    echo "You may need to manually update your docker-compose.yml file"
fi

# Create a README file explaining the integrated setup
cat > INTEGRATED-FRONTEND.md << EOF
# ResumeAI Integrated Frontend Setup

The React frontend has been integrated directly into the FastAPI backend for simplified deployment.

## Benefits

- Eliminates network connectivity issues between frontend and backend
- Simplifies deployment (only one container needed)
- Reduces resource usage
- Better performance on Raspberry Pi and other low-power devices

## How It Works

1. The React frontend is built as a static site
2. The built files are served directly by FastAPI
3. All API requests use relative paths (/api/...)
4. FastAPI handles both the API and serving the frontend files

## Updating the Frontend

If you make changes to the frontend code:

1. Edit the files in the frontend directory
2. Rebuild the frontend:
   ```bash
   cd frontend && npm run build
   ```
3. Restart the backend:
   ```bash
   ./manage.sh backend
   ```

## Reverting to Separate Frontend/Backend

If you want to revert to using separate containers:

1. Edit docker-compose.yml and uncomment the frontend service
2. Run:
   ```bash
   ./manage.sh docker-down
   ./manage.sh docker-up
   ```
EOF

echo "Created INTEGRATED-FRONTEND.md with documentation"

echo "All done! To start the integrated application, run:"
echo "./manage.sh docker-down"
echo "./manage.sh docker-up"
echo ""
echo "The application will be available at: http://localhost:8008"