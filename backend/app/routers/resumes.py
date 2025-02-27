"""
Resumes API Router

This module provides API endpoints for managing resume data.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, UploadFile, File
from typing import List, Optional
import logging
import os

from app.database.base import DatabaseInterface, get_db
from app.models.resume import Resume, ResumeCreate, ResumeUpdate, ResumeList

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

@router.get("/", response_model=ResumeList)
async def get_resumes(
    skip: int = Query(0, description="Number of items to skip"),
    limit: int = Query(100, description="Number of items to return"),
    db: DatabaseInterface = Depends(get_db)
):
    """
    Get a list of resumes with pagination.
    """
    try:
        resumes = await db.get_all_resumes()
        
        # Apply pagination
        total = len(resumes)
        resumes = resumes[skip:skip+limit]
        
        return ResumeList(items=resumes, total=total)
    except Exception as e:
        logger.error(f"Error getting resumes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting resumes: {str(e)}")

@router.get("/{resume_id}", response_model=Resume)
async def get_resume(
    resume_id: str = Path(..., description="The ID of the resume to get"),
    db: DatabaseInterface = Depends(get_db)
):
    """
    Get a single resume by ID.
    """
    try:
        resume = await db.get_resume(resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail=f"Resume with ID {resume_id} not found")
        return resume
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting resume {resume_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting resume: {str(e)}")

@router.post("/", response_model=Resume, status_code=201)
async def create_resume(
    resume: ResumeCreate,
    db: DatabaseInterface = Depends(get_db)
):
    """
    Create a new resume from JSON data.
    """
    # This endpoint would be used for direct JSON upload of resume data
    # For PDF upload, use the /upload endpoint
    try:
        # Not implemented yet as we need to adapt the database interfaces
        raise HTTPException(status_code=501, detail="Not implemented yet")
    except Exception as e:
        logger.error(f"Error creating resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating resume: {str(e)}")

@router.post("/upload", response_model=Resume, status_code=201)
async def upload_resume(
    name: str = Query(..., description="Name of the candidate"),
    file: UploadFile = File(...),
    db: DatabaseInterface = Depends(get_db)
):
    """
    Upload a resume PDF file.
    """
    try:
        # Create resumes directory if it doesn't exist
        os.makedirs("backend/app/resumes", exist_ok=True)
        
        # Save the file
        file_path = f"backend/app/resumes/{name}.pdf"
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        # Here we would typically process the PDF to extract text
        # Then create a resume record in the database
        # For now, we'll just return a placeholder
        
        # Not implemented yet as we need to adapt the database interfaces
        raise HTTPException(status_code=501, detail="Not implemented yet")
    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading resume: {str(e)}")

@router.put("/{resume_id}", response_model=Resume)
async def update_resume(
    resume_id: str,
    resume: ResumeUpdate,
    db: DatabaseInterface = Depends(get_db)
):
    """
    Update an existing resume.
    """
    try:
        # Not implemented yet as we need to adapt the database interfaces
        raise HTTPException(status_code=501, detail="Not implemented yet")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating resume {resume_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating resume: {str(e)}")

@router.delete("/{resume_id}", status_code=204)
async def delete_resume(
    resume_id: str,
    db: DatabaseInterface = Depends(get_db)
):
    """
    Delete a resume.
    """
    try:
        # Not implemented yet as we need to adapt the database interfaces
        raise HTTPException(status_code=501, detail="Not implemented yet")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting resume {resume_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting resume: {str(e)}")