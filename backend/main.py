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
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import routers
from app.routers import vacancies, resumes, settings, process, tasks

# Import database
from app.database.base import get_db, init_db

# Create startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on startup
    await init_db()
    
    # Also directly initialize the PostgreSQL database with pgvector
    try:
        from app.db_init import initialize_database, get_connection
        initialize_database()
        print("✅ PostgreSQL with pgvector initialized successfully")
    except Exception as e:
        print(f"⚠️ PostgreSQL initialization error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    yield
    # Clean up resources on shutdown
    pass

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
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(vacancies.router, prefix="/api/vacancies", tags=["vacancies"])
app.include_router(resumes.router, prefix="/api/resumes", tags=["resumes"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(process.router, prefix="/api/process", tags=["process"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])

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