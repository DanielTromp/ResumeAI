"""
Statistics API Router

This module provides API endpoints for getting statistics about the data.
"""

import logging
from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool

from app.db_interfaces.postgres import (
    get_vacancy_statistics, rebuild_vacancy_statistics
)

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

@router.get("/vacancies", status_code=200)
async def get_vacancy_stats_endpoint():
    """
    Get vacancy statistics by status.
    Returns a dictionary with status as key and count as value, plus a 'total' key.
    """
    try:
        # Get the statistics
        stats = await run_in_threadpool(get_vacancy_statistics)
        
        return {
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Error getting vacancy stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting vacancy statistics: {str(e)}")
        
@router.post("/vacancies/rebuild", status_code=200)
async def rebuild_vacancy_stats_endpoint():
    """
    Rebuild the vacancy statistics from scratch.
    This is useful if the statistics are out of sync with the actual data.
    """
    try:
        # Run the potentially blocking database operation
        success = await run_in_threadpool(rebuild_vacancy_statistics)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to rebuild vacancy statistics")
            
        # Get the updated statistics
        stats = await run_in_threadpool(get_vacancy_statistics)
        
        return {
            "message": "Vacancy statistics rebuilt successfully",
            "statistics": stats
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rebuilding vacancy statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error rebuilding vacancy statistics: {str(e)}")