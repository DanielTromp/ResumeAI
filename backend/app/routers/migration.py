"""
Migration API Router

This module provides API endpoints for database migration operations.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
import logging

# Import migration service
from app.services.migration.nocodb_to_postgres import nocodb_to_postgres_service

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

@router.post("/nocodb-to-postgres", response_model=Dict[str, Any])
async def migrate_nocodb_to_postgres(background_tasks: BackgroundTasks):
    """
    Migrate data from NocoDB to PostgreSQL.
    
    This endpoint starts the migration process in the background and returns immediately.
    Check the status with the GET endpoint.
    """
    try:
        # Get current status
        status = nocodb_to_postgres_service.get_status()
        
        # Check if migration is already running
        if status["status"] == "running":
            return {
                "message": "Migration already in progress",
                "status": status
            }
        
        # Start migration in background
        background_tasks.add_task(nocodb_to_postgres_service.migrate_vacancies)
        
        return {
            "message": "Migration started",
            "status": nocodb_to_postgres_service.get_status()
        }
    except Exception as e:
        logger.error(f"Error starting migration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting migration: {str(e)}")

@router.get("/nocodb-to-postgres/status", response_model=Dict[str, Any])
async def get_migration_status():
    """
    Get the status of the migration process.
    """
    try:
        return nocodb_to_postgres_service.get_status()
    except Exception as e:
        logger.error(f"Error getting migration status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting migration status: {str(e)}")