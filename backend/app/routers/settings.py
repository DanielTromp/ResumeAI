"""
Settings API Router

This module provides API endpoints for managing application settings.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Dict, Any, Optional
import logging
import os
from pydantic import BaseModel
from dotenv import load_dotenv

from app.database.base import DatabaseInterface, get_db

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Settings model
class Settings(BaseModel):
    """Application settings model"""
    openai_api_key: Optional[str] = None
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    nocodb_url: Optional[str] = None
    nocodb_token: Optional[str] = None
    nocodb_project: Optional[str] = None
    nocodb_table: Optional[str] = None
    spinweb_user: Optional[str] = None
    spinweb_pass: Optional[str] = None
    excluded_clients: Optional[str] = None
    ai_model: Optional[str] = None
    match_threshold: Optional[float] = None
    match_count: Optional[int] = None
    resume_prompt_template: Optional[str] = None

class SettingsUpdate(BaseModel):
    """Model for updating application settings"""
    openai_api_key: Optional[str] = None
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    nocodb_url: Optional[str] = None
    nocodb_token: Optional[str] = None
    nocodb_project: Optional[str] = None
    nocodb_table: Optional[str] = None
    spinweb_user: Optional[str] = None
    spinweb_pass: Optional[str] = None
    excluded_clients: Optional[str] = None
    ai_model: Optional[str] = None
    match_threshold: Optional[float] = None
    match_count: Optional[int] = None
    resume_prompt_template: Optional[str] = None

@router.get("/", response_model=Settings)
async def get_settings():
    """
    Get application settings.
    
    Note: For security reasons, sensitive values are redacted.
    """
    try:
        # Load environment variables
        load_dotenv()
        
        # Import PROMPT_TEMPLATE
        from app.config import DEFAULT_PROMPT_TEMPLATE
        
        # Create settings object with redacted sensitive values
        settings = Settings(
            openai_api_key="*****" if os.getenv("OPENAI_API_KEY") else None,
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key="*****" if os.getenv("SUPABASE_KEY") else None,
            nocodb_url=os.getenv("NOCODB_URL"),
            nocodb_token="*****" if os.getenv("NOCODB_TOKEN") else None,
            nocodb_project=os.getenv("NOCODB_PROJECT"),
            nocodb_table=os.getenv("NOCODB_TABLE"),
            spinweb_user=os.getenv("SPINWEB_USER"),
            spinweb_pass="*****" if os.getenv("SPINWEB_PASS") else None,
            excluded_clients=os.getenv("EXCLUDED_CLIENTS"),
            ai_model=os.getenv("AI_MODEL", "gpt-4o-mini"),
            match_threshold=float(os.getenv("MATCH_THRESHOLD", "0.75")),
            match_count=int(os.getenv("MATCH_COUNT", "20")),
            resume_prompt_template=os.getenv("RESUME_PROMPT_TEMPLATE", DEFAULT_PROMPT_TEMPLATE)
        )
        
        return settings
    except Exception as e:
        logger.error(f"Error getting settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting settings: {str(e)}")

@router.put("/", response_model=Settings)
async def update_settings(settings: SettingsUpdate):
    """
    Update application settings.
    
    This endpoint updates the .env file with new settings.
    Only provided values (non-None) will be updated.
    """
    try:
        # Load existing environment variables
        load_dotenv()
        
        # Get all current environment variables
        current_env = {}
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    current_env[key] = value.strip('"\'')
        
        # Update with new values
        updates = {k: v for k, v in settings.model_dump().items() if v is not None}
        
        # Map Pydantic model keys to environment variable names
        env_mapping = {
            "openai_api_key": "OPENAI_API_KEY",
            "supabase_url": "SUPABASE_URL",
            "supabase_key": "SUPABASE_KEY",
            "nocodb_url": "NOCODB_URL",
            "nocodb_token": "NOCODB_TOKEN",
            "nocodb_project": "NOCODB_PROJECT",
            "nocodb_table": "NOCODB_TABLE",
            "spinweb_user": "SPINWEB_USER",
            "spinweb_pass": "SPINWEB_PASS",
            "excluded_clients": "EXCLUDED_CLIENTS",
            "ai_model": "AI_MODEL",
            "match_threshold": "MATCH_THRESHOLD",
            "match_count": "MATCH_COUNT",
            "resume_prompt_template": "RESUME_PROMPT_TEMPLATE"
        }
        
        # Update the environment variables
        for key, value in updates.items():
            env_key = env_mapping.get(key)
            if env_key:
                current_env[env_key] = str(value)
        
        # Write back to .env file
        with open(".env", "w") as f:
            for key, value in current_env.items():
                f.write(f"{key}=\"{value}\"\n")
        
        # Return updated settings (with redacted sensitive values)
        return await get_settings()
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating settings: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}