"""
Resume data models

This module defines the Pydantic models for resume data.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class ResumeFile(BaseModel):
    """Model for resume file information"""
    filename: str = Field(..., description="Resume file name")
    filepath: str = Field(..., description="Path to the resume file")
    size: int = Field(..., description="File size in bytes")
    created_at: Optional[datetime] = Field(None, description="File creation timestamp")
    modified_at: Optional[datetime] = Field(None, description="File modification timestamp")
    mime_type: str = Field("application/pdf", description="File MIME type")
    selected: bool = Field(False, description="Whether the resume is selected")

class ResumeBase(BaseModel):
    """Base resume model with common fields"""
    name: str = Field(..., description="Name of the candidate")
    content: Optional[str] = Field(None, description="Resume content")
    file_info: Optional[ResumeFile] = Field(None, description="Resume file information")

class ResumeCreate(ResumeBase):
    """Model for creating a new resume"""
    pass

class ResumeUpdate(BaseModel):
    """Model for updating an existing resume"""
    name: Optional[str] = Field(None, description="Name of the candidate")
    content: Optional[str] = Field(None, description="Resume content")
    selected: Optional[bool] = Field(None, description="Whether the resume is selected")

class Resume(ResumeBase):
    """Complete resume model with all fields"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "John Doe",
                "content": "Experienced software developer...",
                "file_info": {
                    "filename": "John Doe.pdf",
                    "filepath": "/app/resumes/John Doe.pdf",
                    "size": 1024567,
                    "created_at": "2025-05-26T12:00:00",
                    "modified_at": "2025-05-26T12:00:00",
                    "mime_type": "application/pdf",
                    "selected": False
                },
                "created_at": "2025-05-26T12:00:00",
                "updated_at": "2025-05-26T12:00:00"
            }
        }

class ResumeList(BaseModel):
    """Model for returning a list of resumes"""
    items: List[Resume]
    total: int