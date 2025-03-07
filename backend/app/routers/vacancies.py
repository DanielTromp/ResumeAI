"""
Vacancies API Router

This module provides API endpoints for managing vacancy data.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Optional, Any, Dict
import logging
import os
import datetime
import json
import time
from functools import lru_cache
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from app.db_interfaces.postgres import (
    get_all_vacancies, get_vacancy, create_vacancy, update_vacancy, delete_vacancy,
    get_vacancy_statistics, rebuild_vacancy_statistics
)
from app.models.vacancy import Vacancy, VacancyCreate, VacancyUpdate, VacancyList

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Cache variables
CACHE_TTL_SECONDS = 60  # Cache expires after 60 seconds
_vacancies_cache = {
    "data": None,
    "timestamp": 0,
    "is_refreshing": False
}

# Cache helper functions
def get_cached_vacancies():
    """Get vacancies from cache if valid, otherwise return None"""
    current_time = time.time()
    if (_vacancies_cache["data"] is not None and 
        current_time - _vacancies_cache["timestamp"] < CACHE_TTL_SECONDS):
        return _vacancies_cache["data"]
    return None

def set_cached_vacancies(data):
    """Update the vacancies cache"""
    _vacancies_cache["data"] = data
    _vacancies_cache["timestamp"] = time.time()
    _vacancies_cache["is_refreshing"] = False

@router.get("/", response_model=VacancyList)
async def get_vacancies(
    skip: int = Query(0, description="Number of items to skip"),
    limit: int = Query(10000, description="Number of items to return"),
    status: Optional[str] = Query(None, description="Filter by status (None returns all statuses)"),
    force_refresh: bool = Query(False, description="Force refresh from database")
):
    """
    Get a list of vacancies with optional filtering and pagination.
    No default status filter, returns all vacancies. Sort is by Geplaatst date (newest first).
    Uses caching for better performance, with a 60-second TTL.
    """
    try:
        # Log the request
        logger.info(f"Getting vacancies with skip={skip}, limit={limit}, status={status}, force_refresh={force_refresh}")
        logger.info(f"Using PostgreSQL database")
        
        # Try to get from cache unless forced refresh
        all_vacancies = None
        if not force_refresh:
            all_vacancies = get_cached_vacancies()
            if all_vacancies:
                logger.info(f"Retrieved {len(all_vacancies)} vacancies from cache")
        
        # Get vacancy statistics for quick counts without loading all data
        vacancy_stats = None
        try:
            vacancy_stats = await run_in_threadpool(get_vacancy_statistics)
            logger.info(f"Retrieved vacancy statistics: {vacancy_stats}")
        except Exception as stats_error:
            logger.error(f"Error fetching vacancy statistics: {str(stats_error)}")
            # Continue without statistics, will fall back to calculating from vacancies
        
        # If cache miss or forced refresh, fetch from database
        if all_vacancies is None:
            # To avoid multiple simultaneous refreshes, check if already refreshing
            if _vacancies_cache["is_refreshing"]:
                logger.info("Another request is already refreshing the cache, using empty temporary result")
                all_vacancies = {"items": [], "total": 0, "filtered_count": 0}
            else:
                _vacancies_cache["is_refreshing"] = True
                logger.info("Cache miss or forced refresh, fetching from database")
                
                # Run the potentially blocking database operation
                try:
                    # Use run_in_threadpool for synchronous database operations
                    result = await run_in_threadpool(
                        lambda: get_all_vacancies(status, skip, limit)
                    )
                    
                    if not isinstance(result, dict):
                        # Handle old function signature return (just a list)
                        all_vacancies = {"items": result, "total": len(result), "filtered_count": len(result)}
                    else:
                        # New function signature returns a dict with items, total, filtered_count
                        all_vacancies = result
                    
                    # Update the cache with the fresh data
                    set_cached_vacancies(all_vacancies)
                    logger.info(f"Updated cache with {len(all_vacancies.get('items', []))} vacancies from database out of {all_vacancies.get('total', 0)} total")
                except Exception as db_error:
                    _vacancies_cache["is_refreshing"] = False
                    logger.error(f"Error fetching vacancies from database: {str(db_error)}")
                    raise
        
        # Get total counts from the database result or from statistics
        total_all_statuses = all_vacancies.get('total') if isinstance(all_vacancies, dict) else 0
        if total_all_statuses == 0 and vacancy_stats:
            total_all_statuses = vacancy_stats.get('total', 0)
            
        # Get the vacancies items from the database result
        vacancies_items = all_vacancies.get('items', []) if isinstance(all_vacancies, dict) else []
        
        # Get total filtered count from the database result or from statistics
        if status and vacancy_stats:
            total_filtered = vacancy_stats.get(status, 0)
        else:
            total_filtered = total_all_statuses
        
        # We're not doing additional sorting here since the database query is already sorted by created_at DESC
        # Just use the vacancies as they come from the database
        sorted_vacancies = vacancies_items
        logger.info(f"Using database sort order (created_at DESC)")
        
        # No need to apply pagination here as it's already done in the database query
        # Log the number of vacancies we have
        logger.info(f"Retrieved {len(sorted_vacancies)} vacancies (skip={skip}, limit={limit}, total_filtered={total_filtered})")
        
        # Convert integer IDs to strings to match model expectations
        for vacancy in sorted_vacancies:
            if "id" in vacancy and not isinstance(vacancy["id"], str):
                vacancy["id"] = str(vacancy["id"])
            
            # Check for both versions of field name (with and without underscore)
            match_toelichting = vacancy.get("Match Toelichting") or vacancy.get("Match_Toelichting")
            
            # Store in both field names to ensure compatibility
            if match_toelichting:
                try:
                    # Check if it looks like JSON
                    if isinstance(match_toelichting, str) and (
                        match_toelichting.strip().startswith("{") or 
                        match_toelichting.strip().startswith("[")
                    ):
                        # Try to parse JSON and convert to markdown
                        match_data = json.loads(match_toelichting)
                        
                        # Convert to markdown based on structure
                        if isinstance(match_data, dict):
                            markdown = ""
                            for key, value in match_data.items():
                                markdown += f"## {key}\n"
                                if isinstance(value, list):
                                    for item in value:
                                        markdown += f"- {item}\n"
                                elif isinstance(value, dict):
                                    for subkey, subvalue in value.items():
                                        markdown += f"### {subkey}\n{subvalue}\n\n"
                                else:
                                    markdown += f"{value}\n\n"
                            
                            # Store in both field names for compatibility
                            vacancy["Match Toelichting"] = markdown
                            vacancy["Match_Toelichting"] = markdown
                    else:
                        # Not JSON, just copy to both fields
                        vacancy["Match Toelichting"] = match_toelichting
                        vacancy["Match_Toelichting"] = match_toelichting
                    
                except Exception as e:
                    logger.warning(f"Failed to convert Match Toelichting to markdown: {e}")
                    # Keep original if conversion fails
                    vacancy["Match Toelichting"] = match_toelichting
                    vacancy["Match_Toelichting"] = match_toelichting
        
        # Fix any datetime objects before returning
        for vacancy in sorted_vacancies:
            for key, value in vacancy.items():
                if isinstance(value, datetime.datetime):
                    vacancy[key] = value.strftime("%Y-%m-%d")
        
        # Return response with both total counts
        response = VacancyList(
            items=sorted_vacancies, 
            total=total_filtered,
            total_all=total_all_statuses
        )
            
        logger.info(f"Returning {len(sorted_vacancies)} vacancies with total_filtered={total_filtered}, total_all={total_all_statuses}")
        
        return response
    except Exception as e:
        logger.error(f"Error getting vacancies: {str(e)}", exc_info=True)
        
        # Create a more detailed error message
        error_type = type(e).__name__
        error_details = str(e)
        
        # Check for specific error types and provide more helpful messages
        if "connection" in error_details.lower() or "timeout" in error_details.lower():
            message = f"Failed to connect to the database. Please check your database configuration and connectivity."
        elif "permission" in error_details.lower() or "access" in error_details.lower():
            message = f"Permission denied when accessing the database. Please check your authentication credentials."
        elif "not found" in error_details.lower():
            message = f"Resource not found in the database. Please check your table or collection names."
        else:
            message = f"Error getting vacancies: {error_type} - {error_details}"
        
        logger.error(f"Returning error to client: {message}")
        raise HTTPException(status_code=500, detail=message)

# Define helper functions for catching errors in direct PostgreSQL operations
def handle_db_error(e, operation):
    """Handle database errors with user-friendly messages"""
    error_details = str(e).lower()
    error_type = type(e).__name__
    
    if "connection" in error_details:
        message = f"Failed to connect to the database. Please check your database configuration and connectivity."
    elif "permission" in error_details or "access" in error_details:
        message = f"Permission denied when accessing the database. Please check your authentication credentials."
    elif "not found" in error_details:
        message = f"Resource not found in the database. Please check that the vacancy exists."
    else:
        message = f"Error during {operation}: {error_type} - {error_details}"
    
    logger.error(f"Database error: {message}")
    return message

@router.get("/{vacancy_id}")  # Remove response_model for debugging
async def get_vacancy_endpoint(
    vacancy_id: str = Path(..., description="The ID of the vacancy to get")
):
    """
    Get a single vacancy by ID.
    Uses caching for better performance.
    """
    try:
        # Use run_in_threadpool for the synchronous database operation
        vacancy_data = await run_in_threadpool(lambda: get_vacancy(vacancy_id))
        if not vacancy_data:
            raise HTTPException(status_code=404, detail=f"Vacancy with ID {vacancy_id} not found")
        
        # Convert datetime objects to strings and ensure ID is a string
        for key, value in vacancy_data.items():
            if isinstance(value, datetime.datetime):
                vacancy_data[key] = value.strftime("%Y-%m-%d")
            elif key == 'id' and not isinstance(value, str):
                vacancy_data[key] = str(value)
        
        # Check for both versions of field name (with and without underscore)
        match_toelichting = vacancy_data.get("Match Toelichting") or vacancy_data.get("Match_Toelichting")
        
        # Store in both field names to ensure compatibility
        if match_toelichting:
            try:
                # Check if it looks like JSON
                if isinstance(match_toelichting, str) and (
                    match_toelichting.strip().startswith("{") or 
                    match_toelichting.strip().startswith("[")
                ):
                    # Try to parse JSON and convert to markdown
                    match_data = json.loads(match_toelichting)
                    
                    # Convert to markdown based on structure
                    if isinstance(match_data, dict):
                        markdown = ""
                        for key, value in match_data.items():
                            markdown += f"## {key}\n"
                            if isinstance(value, list):
                                for item in value:
                                    markdown += f"- {item}\n"
                            elif isinstance(value, dict):
                                for subkey, subvalue in value.items():
                                    markdown += f"### {subkey}\n{subvalue}\n\n"
                            else:
                                markdown += f"{value}\n\n"
                        
                        # Store in both field names for compatibility
                        vacancy_data["Match Toelichting"] = markdown
                        vacancy_data["Match_Toelichting"] = markdown
                else:
                    # Not JSON, just copy to both fields
                    vacancy_data["Match Toelichting"] = match_toelichting
                    vacancy_data["Match_Toelichting"] = match_toelichting
                
            except Exception as e:
                logger.warning(f"Failed to convert Match Toelichting to markdown: {e}")
                # Keep original if conversion fails
                vacancy_data["Match Toelichting"] = match_toelichting
                vacancy_data["Match_Toelichting"] = match_toelichting
        
        # Add debugging log
        logger.info(f"Returning vacancy data: {vacancy_data}")
        
        # Make sure we have all required fields
        required_fields = ["URL", "id", "Status"]
        for field in required_fields:
            if field not in vacancy_data:
                logger.error(f"Required field '{field}' missing from vacancy data")
                # Add fallback values for critical fields
                if field == "URL":
                    vacancy_data[field] = "unknown-url"
                elif field == "id":
                    vacancy_data[field] = str(vacancy_id)
                elif field == "Status":
                    vacancy_data[field] = "Unknown"
        
        return vacancy_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vacancy {vacancy_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting vacancy: {str(e)}")

@router.post("/", response_model=Vacancy, status_code=201)
async def create_vacancy_endpoint(
    vacancy: VacancyCreate
):
    """
    Create a new vacancy.
    """
    try:
        # Convert Pydantic model to dict
        vacancy_data = vacancy.model_dump()
        
        # Create the vacancy using run_in_threadpool for synchronous database operation
        created_vacancy = await run_in_threadpool(lambda: create_vacancy(vacancy_data))
        return created_vacancy
    except Exception as e:
        logger.error(f"Error creating vacancy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating vacancy: {str(e)}")

@router.put("/{vacancy_id}", response_model=Vacancy)
async def update_vacancy_endpoint(
    vacancy_id: str,
    vacancy: VacancyUpdate
):
    """
    Update an existing vacancy.
    """
    try:
        # Check if vacancy exists using run_in_threadpool
        existing_vacancy = await run_in_threadpool(lambda: get_vacancy(vacancy_id))
        if not existing_vacancy:
            raise HTTPException(status_code=404, detail=f"Vacancy with ID {vacancy_id} not found")
        
        # Convert Pydantic model to dict and filter out None values
        update_data = {k: v for k, v in vacancy.model_dump().items() if v is not None}
        
        # Update the vacancy using run_in_threadpool
        updated_vacancy = await run_in_threadpool(lambda: update_vacancy(vacancy_id, update_data))
        return updated_vacancy
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating vacancy {vacancy_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating vacancy: {str(e)}")

@router.delete("/{vacancy_id}", status_code=204)
async def delete_vacancy_endpoint(
    vacancy_id: str
):
    """
    Delete a vacancy.
    """
    try:
        # Check if vacancy exists
        existing_vacancy = await run_in_threadpool(lambda: get_vacancy(vacancy_id))
        if not existing_vacancy:
            raise HTTPException(status_code=404, detail=f"Vacancy with ID {vacancy_id} not found")
        
        # Delete the vacancy
        success = await run_in_threadpool(lambda: delete_vacancy(vacancy_id))
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to delete vacancy {vacancy_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting vacancy {vacancy_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting vacancy: {str(e)}")

@router.get("/stats", status_code=200)
async def get_statistics_endpoint():
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
        logger.error(f"Error getting vacancy statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting vacancy statistics: {str(e)}")
        
@router.post("/rebuild-stats", status_code=200)
async def rebuild_statistics_endpoint():
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