"""
Resume data models

This module defines the Pydantic models for resume data.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class ResumeBase(BaseModel):
    """Base resume model with common fields"""
    name: str = Field(..., description="Name of the candidate")
    content: Optional[str] = Field(None, description="Resume content")

class ResumeCreate(ResumeBase):
    """Model for creating a new resume"""
    pass

class ResumeUpdate(BaseModel):
    """Model for updating an existing resume"""
    name: Optional[str] = Field(None, description="Name of the candidate")
    content: Optional[str] = Field(None, description="Resume content")

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
                "created_at": "2025-05-26T12:00:00",
                "updated_at": "2025-05-26T12:00:00"
            }
        }

class ResumeList(BaseModel):
    """Model for returning a list of resumes"""
    items: List[Resume]
    total: int