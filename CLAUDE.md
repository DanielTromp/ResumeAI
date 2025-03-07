# ResumeAI Project Guidelines

## Installation Guide

### Prerequisites
- Python 3.10 or higher
- Node.js 18.x or higher (important: some dependencies require Node.js 18+)
- npm 8.x or higher
- Git (for cloning the repository)

### First-time Setup

#### Backend Setup (MacOS/Linux)
```bash
# Clone the repository (if you haven't already)
git clone https://github.com/YourUsername/ResumeAI.git
cd ResumeAI

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

#### Backend Setup (Windows)
```bash
# Clone the repository (if you haven't already)
git clone https://github.com/YourUsername/ResumeAI.git
cd ResumeAI

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\activate

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

#### Frontend Setup (All platforms)
```bash
# Navigate to the frontend directory
cd frontend

# Install frontend dependencies
npm install

# Fix known vulnerabilities (non-breaking)
npm audit fix

# If you see warnings about Node.js version compatibility or security issues:
# 1. Make sure you're using Node.js 18.x or higher
# 2. Consider running a full security fix (may require manual intervention)
npm audit fix --force
```

### Running the Application

#### Configuration (optional)
- The default backend port is 8008. If needed, change it in:
  - Backend: `main.py` - Edit the line `uvicorn.run("main:app", host="0.0.0.0", port=8008, reload=True)`
  - Frontend: `package.json` - Edit the proxy setting: `"proxy": "http://localhost:8008"`

#### Starting the Backend
```bash
# Make sure your virtual environment is activated
# From the project root:
cd backend
python main.py

# The backend will start on http://localhost:8008
```

#### Starting the Frontend
```bash
# In a new terminal, from the project root:
cd frontend
npm start

# The frontend will start on http://localhost:3000
```

#### Accessing the Application
- Open a web browser and navigate to http://localhost:3000

## Production Deployment Guide

This guide explains how to deploy ResumeAI in a production environment.

### Backend Deployment

#### Option 1: Deploying with Gunicorn (Recommended)

1. Install Gunicorn:
```bash
pip install gunicorn
```

2. Create a production configuration file (e.g., `prod_config.py`):
```python
# Production configuration for ResumeAI
bind = "0.0.0.0:8008"
workers = 4  # Number of worker processes (2-4 × num_cores is recommended)
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 5
errorlog = "/var/log/gunicorn/error.log"
accesslog = "/var/log/gunicorn/access.log"
loglevel = "warning"
```

3. Start the backend with Gunicorn:
```bash
cd backend
gunicorn -c prod_config.py main:app
```

4. For automatic startup and management, use systemd (Linux):

Create a systemd service file in `/etc/systemd/system/resumeai-backend.service`:
```
[Unit]
Description=ResumeAI Backend Service
After=network.target

[Service]
User=yourusername
Group=yourgroup
WorkingDirectory=/path/to/ResumeAI/backend
ExecStart=/path/to/venv/bin/gunicorn -c prod_config.py main:app
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl enable resumeai-backend
sudo systemctl start resumeai-backend
```

#### Option 2: Deploying with Docker

1. Create a Dockerfile in the backend directory:
```Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

COPY . .

# Install Playwright browsers
RUN playwright install chromium

EXPOSE 8008

CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8008", "main:app"]
```

2. Build and run the Docker container:
```bash
docker build -t resumeai-backend .
docker run -d -p 8008:8008 --name resumeai-backend resumeai-backend
```

### Frontend Deployment

#### Option 1: Static Build Deployment (Recommended)

1. Create a production build:
```bash
cd frontend
npm run build
```

2. Serve the static files with Nginx:

Install Nginx:
```bash
# Ubuntu/Debian
sudo apt install nginx

# CentOS/RHEL
sudo yum install nginx
```

Create an Nginx configuration in `/etc/nginx/sites-available/resumeai`:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/ResumeAI/frontend/build;
    index index.html;

    # Serve static files
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to the backend
    location /api {
        proxy_pass http://localhost:8008;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable the site and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/resumeai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Option 2: Deploying with Docker

1. Create a Dockerfile in the frontend directory:
```Dockerfile
# Build stage
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

2. Create an nginx.conf file:
```nginx
server {
    listen 80;
    
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://backend:8008;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

3. Build and run the Docker container:
```bash
docker build -t resumeai-frontend .
docker run -d -p 80:80 --name resumeai-frontend resumeai-frontend
```

### Full-Stack Deployment with Docker Compose

Create a `docker-compose.yml` file in the project root:
```yaml
version: '3'

services:
  backend:
    build: ./backend
    ports:
      - "8008:8008"
    volumes:
      - ./backend/app/data:/app/app/data
      - ./backend/app/resumes:/app/app/resumes

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  data:
  resumes:
```

Deploy with Docker Compose:
```bash
docker-compose up -d
```

### Production Security Considerations

1. **Authentication**:
   - Basic Authentication is enabled on the frontend through Nginx
   - Default credentials: username `admin`, password `resumeai`
   - Change these by setting environment variables:
     ```
     AUTH_USERNAME=your_username
     AUTH_PASSWORD=your_password
     ```
   - Only protects the frontend UI, API endpoints remain accessible for automation
   
2. **HTTPS Setup**:
   - Obtain an SSL certificate (e.g., Let's Encrypt)
   - Configure Nginx for HTTPS or use Cloudflare Tunnel
   
3. **Environment Variables**:
   - Use environment variables for secrets, not .env files
   - Consider using a secrets manager for API keys
   
4. **API Authentication**:
   - Basic Authentication protects all API endpoints
   - Configure CORS to allow only specific origins

4. **Backups**:
   - Set up regular backups of the data directory
   - Backup resume files and database

### Monitoring and Maintenance

1. **Monitoring**:
   - Set up logging with a tool like ELK Stack or Graylog
   - Monitor server resources (CPU, memory, disk)
   
2. **Updates**:
   - Establish a process for safe updates
   - Test updates in a staging environment first
   
3. **Scaling**:
   - Consider using a load balancer for multiple backend instances
   - Monitor performance and scale as needed

## Commands
- **Run Combined Process:** `cd backend && python -m app.combined_process`
- **Install Backend Dependencies:** `pip install -r backend/requirements.txt`
- **Install Frontend Dependencies:** `cd frontend && npm install`
- **Install Playwright:** `playwright install`
- **Activate Virtual Environment:** `source venv/bin/activate` (Mac/Linux) or `.\venv\Scripts\activate` (Windows)

## Code Style Guidelines
- **Imports:** Group in order: standard library, third-party, project-specific
- **Docstrings:** Use """triple quotes""" with function description, parameters, and return values
- **Error Handling:** Use try/except with specific exception types and logging
- **Logging:** Use the progress_logger for user feedback and standard logger for errors
- **Naming:** Use snake_case for variables/functions, CamelCase for classes
- **Environment Variables:** Store sensitive data in .env file, load with python-dotenv

## Project Structure
- **03_ONS:** Latest version using NocoDB backend
- **02_OCL:** Version using local storage (LanceDB)
- **01_OAS:** Version using Airtable backend

## Key Dependencies
- OpenAI API for embeddings and matching (GPT-4o-mini)
- Playwright for web scraping
- Supabase for vector storage
- NocoDB for vacancy storage and tracking