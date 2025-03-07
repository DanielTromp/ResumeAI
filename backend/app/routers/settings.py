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

from app.db_init import get_connection

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Import database service
from app.services.database_service import db_service, DatabaseService

# Settings model
class Settings(BaseModel):
    """Application settings model"""
    openai_api_key: Optional[str] = None
    
    # PostgreSQL settings
    pg_host: Optional[str] = None
    pg_port: Optional[str] = None
    pg_user: Optional[str] = None
    pg_password: Optional[str] = None
    pg_database: Optional[str] = None
    
    # Spinweb settings
    spinweb_user: Optional[str] = None
    spinweb_pass: Optional[str] = None
    
    # Matching settings
    excluded_clients: Optional[str] = None
    ai_model: Optional[str] = None
    match_threshold: Optional[float] = None
    match_count: Optional[int] = None
    resume_prompt_template: Optional[str] = None
    
    # Scheduler settings
    scheduler_enabled: Optional[bool] = None
    scheduler_start_hour: Optional[int] = None
    scheduler_end_hour: Optional[int] = None
    scheduler_interval_minutes: Optional[int] = None
    scheduler_days: Optional[str] = None

class SettingsUpdate(BaseModel):
    """Model for updating application settings"""
    openai_api_key: Optional[str] = None
    
    # PostgreSQL settings
    pg_host: Optional[str] = None
    pg_port: Optional[str] = None
    pg_user: Optional[str] = None
    pg_password: Optional[str] = None
    pg_database: Optional[str] = None
    
    # Spinweb settings
    spinweb_user: Optional[str] = None
    spinweb_pass: Optional[str] = None
    
    # Matching settings
    excluded_clients: Optional[str] = None
    ai_model: Optional[str] = None
    match_threshold: Optional[float] = None
    match_count: Optional[int] = None
    resume_prompt_template: Optional[str] = None
    
    # Scheduler settings
    scheduler_enabled: Optional[bool] = None
    scheduler_start_hour: Optional[int] = None
    scheduler_end_hour: Optional[int] = None
    scheduler_interval_minutes: Optional[int] = None
    scheduler_days: Optional[str] = None

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
            
            # PostgreSQL settings
            pg_host=os.getenv("PG_HOST", "localhost"),
            pg_port=os.getenv("PG_PORT", "5432"),
            pg_user=os.getenv("PG_USER", "postgres"),
            pg_password="*****" if os.getenv("PG_PASSWORD") else None,
            pg_database=os.getenv("PG_DATABASE", "resumeai"),
            
            # Spinweb settings
            spinweb_user=os.getenv("SPINWEB_USER"),
            spinweb_pass="*****" if os.getenv("SPINWEB_PASS") else None,
            
            # Matching settings
            excluded_clients=os.getenv("EXCLUDED_CLIENTS"),
            ai_model=os.getenv("AI_MODEL", "gpt-4o-mini"),
            match_threshold=float(os.getenv("MATCH_THRESHOLD", "0.75")),
            match_count=int(os.getenv("MATCH_COUNT", "20")),
            resume_prompt_template=os.getenv("RESUME_PROMPT_TEMPLATE", DEFAULT_PROMPT_TEMPLATE),
            
            # Scheduler settings
            scheduler_enabled=os.getenv("SCHEDULER_ENABLED", "false").lower() == "true",
            scheduler_start_hour=int(os.getenv("SCHEDULER_START_HOUR", "6")),
            scheduler_end_hour=int(os.getenv("SCHEDULER_END_HOUR", "20")),
            scheduler_interval_minutes=int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "60")),
            scheduler_days=os.getenv("SCHEDULER_DAYS", "mon,tue,wed,thu,fri")
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
        
        # Map Pydantic model keys to environment variable names and their "masked" state in the UI
        env_mapping = {
            "openai_api_key": {"env_key": "OPENAI_API_KEY", "is_masked": True},
            
            # PostgreSQL settings
            "pg_host": {"env_key": "PG_HOST", "is_masked": False},
            "pg_port": {"env_key": "PG_PORT", "is_masked": False},
            "pg_user": {"env_key": "PG_USER", "is_masked": False},
            "pg_password": {"env_key": "PG_PASSWORD", "is_masked": True},
            "pg_database": {"env_key": "PG_DATABASE", "is_masked": False},
            
            # Spinweb settings
            "spinweb_user": {"env_key": "SPINWEB_USER", "is_masked": False},
            "spinweb_pass": {"env_key": "SPINWEB_PASS", "is_masked": True},
            
            # Matching settings
            "excluded_clients": {"env_key": "EXCLUDED_CLIENTS", "is_masked": False},
            "ai_model": {"env_key": "AI_MODEL", "is_masked": False},
            "match_threshold": {"env_key": "MATCH_THRESHOLD", "is_masked": False},
            "match_count": {"env_key": "MATCH_COUNT", "is_masked": False},
            "resume_prompt_template": {"env_key": "RESUME_PROMPT_TEMPLATE", "is_masked": False},
            
            # Scheduler settings
            "scheduler_enabled": {"env_key": "SCHEDULER_ENABLED", "is_masked": False},
            "scheduler_start_hour": {"env_key": "SCHEDULER_START_HOUR", "is_masked": False},
            "scheduler_end_hour": {"env_key": "SCHEDULER_END_HOUR", "is_masked": False},
            "scheduler_interval_minutes": {"env_key": "SCHEDULER_INTERVAL_MINUTES", "is_masked": False},
            "scheduler_days": {"env_key": "SCHEDULER_DAYS", "is_masked": False}
        }
        
        # Filter out "masked" values that weren't actually changed
        filtered_updates = {}
        for key, value in settings.model_dump().items():
            if value is None:
                continue
            
            mapping = env_mapping.get(key)
            if not mapping:
                continue
                
            # If this is a masked field (like a password), and the value is "*****",
            # then it wasn't really changed - the UI just sent back the masked value
            if mapping["is_masked"] and value == "*****":
                logger.info(f"Skipping masked field {key} with value '*****' (not actually changed)")
                continue
                
            # Otherwise, this field was actually changed
            filtered_updates[key] = value
        
        logger.info(f"Actually updating {len(filtered_updates)} fields: {list(filtered_updates.keys())}")
        
        # Update the environment variables
        for key, value in filtered_updates.items():
            mapping = env_mapping.get(key)
            if mapping:
                env_key = mapping["env_key"]
                current_env[env_key] = str(value)
        
        # Write back to .env file, preserving format for sensitive fields
        # Get the original .env content to keep the format for unchanged lines
        original_env_lines = []
        try:
            with open(".env", "r") as f:
                original_env_lines = f.readlines()
        except Exception as read_error:
            logger.warning(f"Could not read original .env format: {str(read_error)}")
        
        # Create a mapping of keys to their original lines (with formatting)
        original_line_map = {}
        for line in original_env_lines:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key = line.split("=", 1)[0].strip()
                original_line_map[key] = line
        
        # Write back to .env file
        with open(".env", "w") as f:
            for key, value in current_env.items():
                # Check if the key was in the filtered updates
                env_key_in_updates = False
                for model_key, mapping in env_mapping.items():
                    if mapping["env_key"] == key and model_key in filtered_updates:
                        env_key_in_updates = True
                        break
                
                # If the key wasn't updated, use the original line format
                if not env_key_in_updates and key in original_line_map:
                    f.write(f"{original_line_map[key]}\n")
                else:
                    # For updated keys, or if we don't have the original format,
                    # use the standard format
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

@router.get("/database/status")
async def get_database_status():
    """
    Get the status of the PostgreSQL database connection.
    """
    try:
        # Check connection to PostgreSQL
        status = db_service.get_connection_status()
        
        # Add resume counts
        counts = {}
        
        # Create independent database service for counting
        if status.get("postgres", False):
            try:
                # Create a dedicated service instance for this query
                postgres_service = DatabaseService()
                counts["postgres"] = postgres_service.count_resumes()
            except Exception as e:
                logger.warning(f"Error counting postgres resumes: {str(e)}")
                counts["postgres"] = None
        
        # Add counts to status
        status["resume_counts"] = counts
        status["current_provider"] = "postgres"
        
        return status
    except Exception as e:
        logger.error(f"Error getting database status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting database status: {str(e)}")