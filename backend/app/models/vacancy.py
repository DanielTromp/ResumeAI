"""
Vacancy data models

This module defines the Pydantic models for vacancy data.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class VacancyBase(BaseModel):
    """Base vacancy model with common fields"""
    URL: str = Field(..., description="The URL of the vacancy")
    Status: Optional[str] = Field("Nieuw", description="The status of the vacancy")
    Functie: Optional[str] = Field(None, description="Job title")
    Klant: Optional[str] = Field(None, description="Client name")
    Branche: Optional[str] = Field(None, description="Industry sector")
    Regio: Optional[str] = Field(None, description="Region/location")
    Uren: Optional[str] = Field(None, description="Working hours")
    Tarief: Optional[str] = Field(None, description="Hourly rate")
    Geplaatst: Optional[str] = Field(None, description="Date posted")
    Sluiting: Optional[str] = Field(None, description="Closing date")
    Functieomschrijving: Optional[str] = Field(None, description="Job description")
    Model: Optional[str] = Field(None, description="AI model used for matching")
    Version: Optional[str] = Field(None, description="Software version")

class VacancyCreate(VacancyBase):
    """Model for creating a new vacancy"""
    pass

class VacancyUpdate(BaseModel):
    """Model for updating an existing vacancy"""
    URL: Optional[str] = Field(None, description="The URL of the vacancy")
    Status: Optional[str] = Field(None, description="The status of the vacancy")
    Functie: Optional[str] = Field(None, description="Job title")
    Klant: Optional[str] = Field(None, description="Client name")
    Branche: Optional[str] = Field(None, description="Industry sector")
    Regio: Optional[str] = Field(None, description="Region/location")
    Uren: Optional[str] = Field(None, description="Working hours")
    Tarief: Optional[str] = Field(None, description="Hourly rate")
    Geplaatst: Optional[str] = Field(None, description="Date posted")
    Sluiting: Optional[str] = Field(None, description="Closing date")
    Functieomschrijving: Optional[str] = Field(None, description="Job description")
    Top_Match: Optional[int] = Field(None, description="Highest match percentage")
    Match_Toelichting: Optional[str] = Field(None, description="Match explanation")
    Checked_resumes: Optional[str] = Field(None, description="List of checked resumes")
    Model: Optional[str] = Field(None, description="AI model used for matching")
    Version: Optional[str] = Field(None, description="Software version")

class Vacancy(VacancyBase):
    """Complete vacancy model with all fields"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    Top_Match: Optional[int] = Field(None, description="Highest match percentage")
    Match_Toelichting: Optional[str] = Field(None, description="Match explanation")
    Checked_resumes: Optional[str] = Field(None, description="List of checked resumes")
    
    class Config:
        # Allow additional fields
        extra = "allow"
        
        # Example schema
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "URL": "spinweb.nl/aanvraag/12345",
                "Status": "Nieuw",
                "Functie": "Python Developer",
                "Klant": "Example Company",
                "Branche": "IT",
                "Regio": "Amsterdam",
                "Uren": "40",
                "Tarief": "€80-€100",
                "Geplaatst": "2025-05-26",
                "Sluiting": "2025-06-26",
                "Functieomschrijving": "Detailed job description...",
                "Top_Match": 85,
                "Match_Toelichting": "Match explanation...",
                "Match Toelichting": "Match explanation...",
                "Checked_resumes": "John Doe, Jane Smith",
                "Model": "gpt-4o-mini",
                "Version": "1.0.0"
            }
        }

class VacancyList(BaseModel):
    """Model for returning a list of vacancies"""
    items: List[Vacancy]
    total: int
    total_all: Optional[int] = None
    
    class Config:
        # Allow extra fields for backward compatibility
        extra = "allow"