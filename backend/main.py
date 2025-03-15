#!/usr/bin/env python3
"""
ResumeAI FastAPI Backend

This is the main entry point for the FastAPI backend that provides API routes
for managing vacancies and resume matching.

Author: Daniel Tromp
Email: drpgmtromp@gmail.com
Version: 1.0.0
Created: 2025-05-26
License: MIT
Repository: https://github.com/DanielTromp/ResumeAI
"""

import os
import base64
import secrets
import time
import shutil
from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Import routers
from app.routers import vacancies, resumes, settings, process, tasks, statistics

# Import db_init for PostgreSQL database initialization
from app.db_init import initialize_database, get_connection

# Import database utilities
from app.db_interfaces.postgres import rebuild_vacancy_statistics

# Import scheduler service
from app.services.scheduler_service import scheduler_service

# Create startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize PostgreSQL database with pgvector
    try:
        initialize_database()
        print("✅ PostgreSQL with pgvector initialized successfully")
        
        # Rebuild vacancy statistics to ensure they're accurate
        try:
            rebuild_vacancy_statistics()
            print("✅ Vacancy statistics rebuilt successfully")
        except Exception as stats_error:
            print(f"⚠️ Error rebuilding vacancy statistics: {str(stats_error)}")
    except Exception as e:
        print(f"⚠️ PostgreSQL initialization error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Start the scheduler if enabled
    try:
        if scheduler_service.enabled:
            scheduler_service.start()
            print(f"✅ Scheduler started with {len(scheduler_service.days)} active days")
        else:
            print("⚠️ Scheduler is disabled. Enable it in settings to automatically run the process.")
    except Exception as e:
        print(f"⚠️ Error starting scheduler: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("✅ Application started successfully")
    yield
    
    # Clean up resources on shutdown
    try:
        if scheduler_service.is_running:
            scheduler_service.stop()
            print("✅ Scheduler stopped")
    except Exception as e:
        print(f"⚠️ Error stopping scheduler: {str(e)}")
    
    print("✅ Application shutdown completed")

# Load environment variables
load_dotenv()

# Authentication credentials (read from environment or use defaults)
AUTH_USERNAME = os.getenv("AUTH_USERNAME", "admin")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "resumeai")

# Security utilities
security = HTTPBasic()

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify HTTP Basic Auth credentials"""
    is_username_correct = secrets.compare_digest(credentials.username, AUTH_USERNAME)
    is_password_correct = secrets.compare_digest(credentials.password, AUTH_PASSWORD)
    
    if not (is_username_correct and is_password_correct):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Authentication middleware
class BasicAuthMiddleware:
    """Middleware for HTTP Basic Authentication"""
    
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        request = Request(scope)
        # Skip auth for /docs, /openapi.json, /redoc, /api/health and static files
        if (request.url.path in ["/docs", "/openapi.json", "/redoc", "/api/health"] or
            request.url.path.startswith("/static/")):
            await self.app(scope, receive, send)
            return
            
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Not authenticated"},
                headers={"WWW-Authenticate": "Basic"},
            )
            await response(scope, receive, send)
            return
        
        # Parse auth header
        try:
            scheme, credentials = auth_header.split()
            if scheme.lower() != "basic":
                response = JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid authentication scheme"},
                    headers={"WWW-Authenticate": "Basic"},
                )
                await response(scope, receive, send)
                return
                
            decoded = base64.b64decode(credentials).decode("utf-8")
            username, password = decoded.split(":")
            
            # Verify credentials
            is_username_correct = secrets.compare_digest(username, AUTH_USERNAME)
            is_password_correct = secrets.compare_digest(password, AUTH_PASSWORD)
            
            if not (is_username_correct and is_password_correct):
                response = JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid credentials"},
                    headers={"WWW-Authenticate": "Basic"},
                )
                await response(scope, receive, send)
                return
        except Exception:
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid authentication credentials"},
                headers={"WWW-Authenticate": "Basic"},
            )
            await response(scope, receive, send)
            return
            
        await self.app(scope, receive, send)

# Create the FastAPI app
app = FastAPI(
    title="ResumeAI API",
    description="API for matching resumes with job vacancies",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:3000", "http://127.0.0.1:3000"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=60 * 60  # Cache preflight requests for 1 hour
)

# Prepare frontend static files directory
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
os.makedirs(FRONTEND_DIR, exist_ok=True)

# Check if we should deploy a production build from the frontend directory
# Try multiple possible build directory locations
possible_build_dirs = [
    # Standard location (outside the app directory)
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "build"),
    # Docker-specific location
    "/frontend/build",
    # Relative to current directory
    os.path.join("frontend", "build"),
    # Mounted volume in Docker
    "/app/frontend/build"
]

found_build_dir = False
for build_dir in possible_build_dirs:
    if os.path.exists(build_dir):
        FRONTEND_BUILD_DIR = build_dir
        found_build_dir = True
        # Skip copying frontend for now to avoid permission issues
        print(f"✅ Found React build directory at {FRONTEND_BUILD_DIR}, but skipping copy to avoid permissions issues")
        break

if not found_build_dir:
    print(f"⚠️ React build directory not found. Checked: {', '.join(possible_build_dirs)}")

# Mount the static files directory if it exists
static_dir = os.path.join(FRONTEND_DIR, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Add authentication middleware
app.add_middleware(BasicAuthMiddleware)

# Include routers
app.include_router(vacancies.router, prefix="/api/vacancies", tags=["vacancies"])
app.include_router(resumes.router, prefix="/api/resumes", tags=["resumes"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(process.router, prefix="/api/process", tags=["process"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(statistics.router, prefix="/api/statistics", tags=["statistics"])

# Root endpoint - serves the React frontend
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the React frontend index.html"""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            return f.read()
    else:
        return HTMLResponse(content="""
        <html>
            <head>
                <title>ResumeAI</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                    h1 { color: #2c3e50; }
                    a { color: #3498db; text-decoration: none; }
                    a:hover { text-decoration: underline; }
                    .container { max-width: 800px; margin: 0 auto; }
                    .card { border: 1px solid #ddd; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Welcome to ResumeAI</h1>
                    <div class="card">
                        <p>The frontend is not yet built. You can:</p>
                        <ul>
                            <li>Build the frontend with: <code>cd frontend && npm run build</code></li>
                            <li>Access the API directly at <a href="/docs">/docs</a></li>
                            <li>Access the backend health check at <a href="/api/health">/api/health</a></li>
                        </ul>
                    </div>
                </div>
            </body>
        </html>
        """)

# Serve frontend assets for React routing
@app.get("/{file_path:path}")
async def serve_frontend_files(file_path: str):
    """Serve any frontend files or return index.html for client-side routing"""
    # We don't need this check anymore as API routes are handled by their own routers
    # Skip API routes
    # if file_path.startswith("api"):
    #     raise HTTPException(status_code=404, detail="API route not found")
        
    # Check if file exists in frontend directory
    full_path = os.path.join(FRONTEND_DIR, file_path)
    if os.path.isfile(full_path):
        return FileResponse(full_path)
    
    # For client-side routing, return index.html
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
        
    # If no index.html exists, return 404
    raise HTTPException(status_code=404, detail="File not found")

# This endpoint was moved above to ensure it's registered before the wildcard route

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8008, reload=True)