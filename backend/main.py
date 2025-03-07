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
from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
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

    async def __call__(self, request: Request, call_next):
        # Skip auth for /docs, /openapi.json and /redoc
        if request.url.path in ["/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)
            
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Not authenticated"},
                headers={"WWW-Authenticate": "Basic"},
            )
        
        # Parse auth header
        try:
            scheme, credentials = auth_header.split()
            if scheme.lower() != "basic":
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid authentication scheme"},
                    headers={"WWW-Authenticate": "Basic"},
                )
                
            decoded = base64.b64decode(credentials).decode("utf-8")
            username, password = decoded.split(":")
            
            # Verify credentials
            is_username_correct = secrets.compare_digest(username, AUTH_USERNAME)
            is_password_correct = secrets.compare_digest(password, AUTH_PASSWORD)
            
            if not (is_username_correct and is_password_correct):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid credentials"},
                    headers={"WWW-Authenticate": "Basic"},
                )
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid authentication credentials"},
                headers={"WWW-Authenticate": "Basic"},
            )
            
        return await call_next(request)

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

# Authentication middleware removed - we'll add it only to the frontend

# Include routers
app.include_router(vacancies.router, prefix="/api/vacancies", tags=["vacancies"])
app.include_router(resumes.router, prefix="/api/resumes", tags=["resumes"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(process.router, prefix="/api/process", tags=["process"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(statistics.router, prefix="/api/statistics", tags=["statistics"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to the ResumeAI API",
        "version": "1.0.0",
        "docs_url": "/docs",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8008, reload=True)