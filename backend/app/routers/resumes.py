"""
Resumes API Router

This module provides API endpoints for managing resume data.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path as FastAPIPath, UploadFile, File, Form
from fastapi.responses import FileResponse
from typing import List, Optional, Dict, Any
import logging
import os
import uuid
import shutil
import datetime
import glob
import PyPDF2
from pathlib import Path as FilePath

from app.models.resume import Resume, ResumeCreate, ResumeUpdate, ResumeList, ResumeFile
from starlette.concurrency import run_in_threadpool

# Set up logging
logger = logging.getLogger(__name__)

# Define resume storage path
RESUME_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resumes")

# Create router
router = APIRouter()

@router.get("/", response_model=ResumeList)
async def get_resumes(
    skip: int = Query(0, description="Number of items to skip"),
    limit: int = Query(100, description="Number of items to return"),
    search: str = Query(None, description="Search term for filtering resumes")
):
    """
    Get a list of resumes with pagination.
    """
    try:
        # Ensure the resume folder exists
        os.makedirs(RESUME_FOLDER, exist_ok=True)
        
        # Get all PDF files from the resume folder
        pdf_files = glob.glob(os.path.join(RESUME_FOLDER, "*.pdf"))
        
        # Build a list of Resume objects
        resumes = []
        for pdf_path in pdf_files:
            try:
                # Get file info
                file_stats = os.stat(pdf_path)
                filename = os.path.basename(pdf_path)
                name = os.path.splitext(filename)[0]
                
                # Extract creation date from PDF metadata if available
                created_date = None
                modified_date = None
                try:
                    with open(pdf_path, 'rb') as pdf_file:
                        pdf_reader = PyPDF2.PdfReader(pdf_file)
                        if pdf_reader.metadata and '/CreationDate' in pdf_reader.metadata:
                            # Parse PDF creation date format
                            creation_str = pdf_reader.metadata['/CreationDate']
                            if creation_str.startswith('D:'):
                                # Format is typically 'D:YYYYMMDDHHMMSSz'
                                year = int(creation_str[2:6])
                                month = int(creation_str[6:8])
                                day = int(creation_str[8:10])
                                hour = int(creation_str[10:12]) if len(creation_str) > 12 else 0
                                minute = int(creation_str[12:14]) if len(creation_str) > 14 else 0
                                second = int(creation_str[14:16]) if len(creation_str) > 16 else 0
                                created_date = datetime.datetime(year, month, day, hour, minute, second)
                except Exception as pdf_error:
                    logger.warning(f"Error extracting PDF metadata from {filename}: {str(pdf_error)}")
                
                # Use file system dates if metadata extraction failed
                if not created_date:
                    created_date = datetime.datetime.fromtimestamp(file_stats.st_ctime)
                
                modified_date = datetime.datetime.fromtimestamp(file_stats.st_mtime)
                
                # Create a ResumeFile object
                file_info = ResumeFile(
                    filename=filename,
                    filepath=pdf_path,
                    size=file_stats.st_size,
                    created_at=created_date,
                    modified_at=modified_date,
                    mime_type="application/pdf",
                    selected=False
                )
                
                # Create the Resume object
                resume = Resume(
                    id=str(uuid.uuid4()),  # Generate a unique ID
                    name=name,  # Use filename without extension as name
                    content=None,  # We don't load content by default
                    file_info=file_info,
                    created_at=created_date,
                    updated_at=modified_date
                )
                
                # Add to results if it matches search term
                if not search or search.lower() in name.lower():
                    resumes.append(resume)
                    
            except Exception as file_error:
                logger.warning(f"Error processing PDF file {pdf_path}: {str(file_error)}")
        
        # Sort by name
        resumes.sort(key=lambda x: x.name)
        
        # Apply pagination
        total = len(resumes)
        paginated_resumes = resumes[skip:skip+limit]
        
        return ResumeList(items=paginated_resumes, total=total)
    
    except Exception as e:
        logger.error(f"Error getting resumes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting resumes: {str(e)}")

@router.get("/{resume_id}", response_model=Resume)
async def get_resume(
    resume_id: str = FastAPIPath(..., description="The ID of the resume to get")
):
    """
    Get a single resume by ID.
    """
    # Since we don't have a persistent database for resumes yet,
    # we'll return a 404 error for now.
    # When we add a database, we'll implement this endpoint properly.
    raise HTTPException(status_code=404, detail=f"Resume with ID {resume_id} not found")

@router.get("/by-name/{name}", response_model=Resume)
async def get_resume_by_name(
    name: str = FastAPIPath(..., description="The name of the resume to get")
):
    """
    Get a single resume by name.
    """
    try:
        # Sanitize the name
        safe_name = os.path.basename(name)
        if safe_name.lower().endswith('.pdf'):
            safe_name = os.path.splitext(safe_name)[0]
            
        # Look for the file
        file_path = os.path.join(RESUME_FOLDER, f"{safe_name}.pdf")
        
        # Check if file exists
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=404, detail=f"Resume file for {safe_name} not found")
            
        # Get file stats
        file_stats = os.stat(file_path)
        created_date = datetime.datetime.fromtimestamp(file_stats.st_ctime)
        modified_date = datetime.datetime.fromtimestamp(file_stats.st_mtime)
        
        # Create file info
        file_info = ResumeFile(
            filename=f"{safe_name}.pdf",
            filepath=file_path,
            size=file_stats.st_size,
            created_at=created_date,
            modified_at=modified_date,
            mime_type="application/pdf",
            selected=False
        )
        
        # Return resume object
        resume = Resume(
            id=str(uuid.uuid4()),
            name=safe_name,
            content=None,
            file_info=file_info,
            created_at=created_date,
            updated_at=modified_date
        )
        
        return resume
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting resume {name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting resume: {str(e)}")

@router.post("/", response_model=Resume, status_code=201)
async def create_resume(
    resume: ResumeCreate
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
    file: UploadFile = File(...),
    name: str = Form(None, description="Name of the candidate (optional)")
):
    """
    Upload a resume PDF file.
    """
    try:
        # Validate file is a PDF
        if not file.content_type == "application/pdf" and not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are accepted")
            
        # Ensure the resumes directory exists
        os.makedirs(RESUME_FOLDER, exist_ok=True)
        
        # Get candidate name from form data or use filename without extension
        if not name:
            name = os.path.splitext(file.filename)[0]
        
        # Create a safe filename
        safe_filename = f"{name}.pdf"
        file_path = os.path.join(RESUME_FOLDER, safe_filename)
        
        # Save the uploaded file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Get file stats
        file_stats = os.stat(file_path)
        created_date = datetime.datetime.fromtimestamp(file_stats.st_ctime)
        modified_date = datetime.datetime.fromtimestamp(file_stats.st_mtime)
        
        # Create file info object
        file_info = ResumeFile(
            filename=safe_filename,
            filepath=file_path,
            size=file_stats.st_size,
            created_at=created_date,
            modified_at=modified_date,
            mime_type="application/pdf",
            selected=False
        )
        
        # Create and return resume object
        resume = Resume(
            id=str(uuid.uuid4()),
            name=name,
            content=None,
            file_info=file_info,
            created_at=created_date,
            updated_at=modified_date
        )
        
        return resume
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading resume: {str(e)}")

@router.get("/download/{filename:path}")
async def download_resume(
    filename: str = FastAPIPath(..., description="The filename of the resume to download")
):
    """
    Download a resume file by filename.
    """
    try:
        # URL decode the filename
        from urllib.parse import unquote
        decoded_filename = unquote(filename)
        
        # Sanitize the filename
        safe_filename = os.path.basename(decoded_filename)
        if not safe_filename.lower().endswith('.pdf'):
            safe_filename += '.pdf'
            
        file_path = os.path.join(RESUME_FOLDER, safe_filename)
        
        # Log debugging info
        logger.info(f"Attempting to download file: {safe_filename}")
        logger.info(f"Full file path: {file_path}")
        logger.info(f"File exists: {os.path.isfile(file_path)}")
        
        # Check if file exists
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=404, detail=f"Resume file {safe_filename} not found")
            
        # Return the file
        return FileResponse(
            path=file_path, 
            filename=safe_filename,
            media_type="application/pdf"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading resume {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error downloading resume: {str(e)}")

@router.put("/{name}", response_model=Resume)
async def update_resume(
    name: str,
    resume: ResumeUpdate
):
    """
    Update an existing resume.
    """
    try:
        # Sanitize the name
        safe_name = os.path.basename(name)
        if safe_name.lower().endswith('.pdf'):
            safe_name = os.path.splitext(safe_name)[0]
            
        # Look for the file
        file_path = os.path.join(RESUME_FOLDER, f"{safe_name}.pdf")
        
        # Check if file exists
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=404, detail=f"Resume file for {safe_name} not found")
        
        # Get file stats
        file_stats = os.stat(file_path)
        created_date = datetime.datetime.fromtimestamp(file_stats.st_ctime)
        modified_date = datetime.datetime.now()
        
        # Create file info with updated selection status if provided
        file_info = ResumeFile(
            filename=f"{safe_name}.pdf",
            filepath=file_path,
            size=file_stats.st_size,
            created_at=created_date,
            modified_at=modified_date,
            mime_type="application/pdf",
            selected=resume.selected if resume.selected is not None else False
        )
        
        # If name was updated, rename the file
        new_name = resume.name
        if new_name and new_name != safe_name:
            # Create new path
            new_path = os.path.join(RESUME_FOLDER, f"{new_name}.pdf")
            
            # Check if new path already exists
            if os.path.exists(new_path):
                raise HTTPException(status_code=409, detail=f"A resume with name '{new_name}' already exists")
                
            # Rename the file
            os.rename(file_path, new_path)
            
            # Update file info
            file_info.filename = f"{new_name}.pdf"
            file_info.filepath = new_path
            safe_name = new_name
        
        # Return updated resume object
        updated_resume = Resume(
            id=str(uuid.uuid4()),  # Generate new ID - in a real DB we'd preserve the original
            name=resume.name if resume.name else safe_name,
            content=resume.content,
            file_info=file_info,
            created_at=created_date,
            updated_at=modified_date
        )
        
        return updated_resume
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating resume {name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating resume: {str(e)}")

@router.delete("/{name}", status_code=204)
async def delete_resume(
    name: str
):
    """
    Delete a resume.
    """
    try:
        # Sanitize the name
        safe_name = os.path.basename(name)
        if safe_name.lower().endswith('.pdf'):
            safe_name = os.path.splitext(safe_name)[0]
            
        # Look for the file
        file_path = os.path.join(RESUME_FOLDER, f"{safe_name}.pdf")
        
        # Check if file exists
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=404, detail=f"Resume file for {safe_name} not found")
            
        # Delete the file
        os.remove(file_path)
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting resume {name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting resume: {str(e)}")

# Endpoints for selection management
@router.post("/select/{name}", status_code=200)
async def select_resume(
    name: str
):
    """
    Mark a resume as selected.
    """
    try:
        # Sanitize the name
        safe_name = os.path.basename(name)
        if safe_name.lower().endswith('.pdf'):
            safe_name = os.path.splitext(safe_name)[0]
            
        # Call the update endpoint with selected=True
        update = ResumeUpdate(selected=True)
        return await update_resume(safe_name, update)
    except Exception as e:
        logger.error(f"Error selecting resume {name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error selecting resume: {str(e)}")

@router.post("/deselect/{name}", status_code=200)
async def deselect_resume(
    name: str
):
    """
    Mark a resume as not selected.
    """
    try:
        # Sanitize the name
        safe_name = os.path.basename(name)
        if safe_name.lower().endswith('.pdf'):
            safe_name = os.path.splitext(safe_name)[0]
            
        # Call the update endpoint with selected=False
        update = ResumeUpdate(selected=False)
        return await update_resume(safe_name, update)
    except Exception as e:
        logger.error(f"Error deselecting resume {name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deselecting resume: {str(e)}")

@router.get("/selected", response_model=ResumeList)
async def get_selected_resumes():
    """
    Get all selected resumes.
    """
    try:
        # Get all resumes
        all_resumes_response = await get_resumes(skip=0, limit=1000, search=None, db=None)
        all_resumes = all_resumes_response.items
        
        # Filter to only selected resumes
        selected_resumes = [resume for resume in all_resumes if resume.file_info and resume.file_info.selected]
        
        return ResumeList(items=selected_resumes, total=len(selected_resumes))
    except Exception as e:
        logger.error(f"Error getting selected resumes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting selected resumes: {str(e)}")