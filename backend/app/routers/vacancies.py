"""
Vacancies API Router

This module provides API endpoints for managing vacancy data.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Optional
import logging
import os
import datetime
import json
import time
from functools import lru_cache
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from app.database.base import DatabaseInterface, get_db
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
    limit: int = Query(100, description="Number of items to return"),
    status: Optional[str] = Query("Open", description="Filter by status (default 'Open')"),
    force_refresh: bool = Query(False, description="Force refresh from database"),
    db: DatabaseInterface = Depends(get_db)
):
    """
    Get a list of vacancies with optional filtering and pagination.
    Default status filter is 'Open'. Sort is by Geplaatst date (newest first).
    Uses caching for better performance, with a 60-second TTL.
    """
    try:
        # Log the request
        logger.info(f"Getting vacancies with skip={skip}, limit={limit}, status={status}, force_refresh={force_refresh}")
        logger.info(f"Database type: {os.getenv('DB_TYPE', 'unknown')}")
        
        # Try to get from cache unless forced refresh
        all_vacancies = None
        if not force_refresh:
            all_vacancies = get_cached_vacancies()
            if all_vacancies:
                logger.info(f"Retrieved {len(all_vacancies)} vacancies from cache")
        
        # If cache miss or forced refresh, fetch from database
        if all_vacancies is None:
            # To avoid multiple simultaneous refreshes, check if already refreshing
            if _vacancies_cache["is_refreshing"]:
                logger.info("Another request is already refreshing the cache, using empty temporary result")
                all_vacancies = []
            else:
                _vacancies_cache["is_refreshing"] = True
                logger.info("Cache miss or forced refresh, fetching from database")
                
                # Run the potentially blocking database operation
                try:
                    # For NocoDBDatabase, get_all_vacancies returns a coroutine that needs to be awaited
                    all_vacancies = await db.get_all_vacancies(force_refresh=True)
                    # Update the cache with the fresh data
                    set_cached_vacancies(all_vacancies)
                    logger.info(f"Updated cache with {len(all_vacancies)} vacancies from database")
                except Exception as db_error:
                    _vacancies_cache["is_refreshing"] = False
                    logger.error(f"Error fetching vacancies from database: {str(db_error)}")
                    raise
        
        # Store total count of ALL vacancies before status filtering
        total_all_statuses = len(all_vacancies)
        
        # Apply filters if provided
        if status:
            filtered_vacancies = [v for v in all_vacancies if v.get("Status") == status]
            logger.info(f"After status filter: {len(filtered_vacancies)} vacancies with status '{status}'")
        else:
            filtered_vacancies = all_vacancies
            logger.info(f"No status filter applied, using all {len(filtered_vacancies)} vacancies")
        
        # Sort by Created date if available, otherwise fallback to Geplaatst
        def get_date_for_sorting(vacancy):
            # First try to use Created field (should be ISO format)
            created_date = vacancy.get("Created time")
            if created_date:
                return created_date
            
            # Fall back to Geplaatst if no Created field
            geplaatst = vacancy.get("Geplaatst")
            if not geplaatst:
                return "1900-01-01"  # Default old date for items without date
            
            # Try to normalize date format for sorting
            try:
                # Check if it's already in ISO format (YYYY-MM-DD)
                if len(geplaatst) >= 10 and geplaatst[4] == '-' and geplaatst[7] == '-':
                    return geplaatst
                
                # Try DD-MM-YYYY format
                if len(geplaatst) >= 10 and geplaatst[2] == '-' and geplaatst[5] == '-':
                    date = datetime.datetime.strptime(geplaatst, "%d-%m-%Y")
                    return date.strftime("%Y-%m-%d")
                
                # Try other common formats
                for fmt in ["%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y", "%d.%m.%Y", "%Y.%m.%d"]:
                    try:
                        date = datetime.datetime.strptime(geplaatst, fmt)
                        return date.strftime("%Y-%m-%d")
                    except ValueError:
                        continue
            except Exception as e:
                logger.warning(f"Error parsing date '{geplaatst}': {str(e)}")
            
            # Return as is if we can't parse
            return geplaatst
        
        # Sort the vacancies (newest first)
        filtered_vacancies = sorted(filtered_vacancies, key=get_date_for_sorting, reverse=True)
        logger.info(f"Sorted vacancies by date (newest first)")
        
        # Calculate total count for pagination of filtered vacancies
        total_filtered = len(filtered_vacancies)
        
        # Apply pagination
        paginated_vacancies = filtered_vacancies[skip:skip+limit]
        logger.info(f"After pagination: {len(paginated_vacancies)} vacancies (skip={skip}, limit={limit}, total_filtered={total_filtered})")
        
        # Convert integer IDs to strings to match model expectations
        for vacancy in paginated_vacancies:
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
        
        # Return response with both total counts
        response = VacancyList(
            items=paginated_vacancies, 
            total=total_filtered,
            total_all=total_all_statuses
        )
            
        logger.info(f"Returning {len(paginated_vacancies)} vacancies with total_filtered={total_filtered}, total_all={total_all_statuses}")
        
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

@lru_cache(maxsize=100)
async def get_vacancy_cached(vacancy_id: str, db: DatabaseInterface):
    """Cached version of db.get_vacancy to improve performance for repeated requests"""
    vacancy = await db.get_vacancy(vacancy_id)
    if not vacancy:
        return None
    return vacancy

@router.get("/{vacancy_id}", response_model=Vacancy)
async def get_vacancy(
    vacancy_id: str = Path(..., description="The ID of the vacancy to get"),
    db: DatabaseInterface = Depends(get_db)
):
    """
    Get a single vacancy by ID.
    Uses caching for better performance.
    """
    try:
        # Try to get from cache
        vacancy = await get_vacancy_cached(vacancy_id, db)
        if not vacancy:
            raise HTTPException(status_code=404, detail=f"Vacancy with ID {vacancy_id} not found")
        
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
        
        return vacancy
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vacancy {vacancy_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting vacancy: {str(e)}")

@router.post("/", response_model=Vacancy, status_code=201)
async def create_vacancy(
    vacancy: VacancyCreate,
    db: DatabaseInterface = Depends(get_db)
):
    """
    Create a new vacancy.
    """
    try:
        # Convert Pydantic model to dict
        vacancy_data = vacancy.model_dump()
        
        # Create the vacancy
        created_vacancy = await db.create_vacancy(vacancy_data)
        return created_vacancy
    except Exception as e:
        logger.error(f"Error creating vacancy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating vacancy: {str(e)}")

@router.put("/{vacancy_id}", response_model=Vacancy)
async def update_vacancy(
    vacancy_id: str,
    vacancy: VacancyUpdate,
    db: DatabaseInterface = Depends(get_db)
):
    """
    Update an existing vacancy.
    """
    try:
        # Check if vacancy exists
        existing_vacancy = await db.get_vacancy(vacancy_id)
        if not existing_vacancy:
            raise HTTPException(status_code=404, detail=f"Vacancy with ID {vacancy_id} not found")
        
        # Convert Pydantic model to dict and filter out None values
        update_data = {k: v for k, v in vacancy.model_dump().items() if v is not None}
        
        # Update the vacancy
        updated_vacancy = await db.update_vacancy(vacancy_id, update_data)
        return updated_vacancy
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating vacancy {vacancy_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating vacancy: {str(e)}")

@router.delete("/{vacancy_id}", status_code=204)
async def delete_vacancy(
    vacancy_id: str,
    db: DatabaseInterface = Depends(get_db)
):
    """
    Delete a vacancy.
    """
    try:
        # Check if vacancy exists
        existing_vacancy = await db.get_vacancy(vacancy_id)
        if not existing_vacancy:
            raise HTTPException(status_code=404, detail=f"Vacancy with ID {vacancy_id} not found")
        
        # Delete the vacancy
        success = await db.delete_vacancy(vacancy_id)
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to delete vacancy {vacancy_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting vacancy {vacancy_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting vacancy: {str(e)}")