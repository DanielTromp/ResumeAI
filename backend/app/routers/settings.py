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

# Import database service
from app.services.database_service import db_service, DatabaseService, SUPABASE_AVAILABLE

# Settings model
class Settings(BaseModel):
    """Application settings model"""
    openai_api_key: Optional[str] = None
    
    # Database settings
    database_provider: Optional[str] = None
    
    # Supabase settings
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    supabase_resume_table: Optional[str] = None
    
    # PostgreSQL settings
    pg_host: Optional[str] = None
    pg_port: Optional[str] = None
    pg_user: Optional[str] = None
    pg_password: Optional[str] = None
    pg_database: Optional[str] = None
    
    # NocoDB settings
    nocodb_url: Optional[str] = None
    nocodb_token: Optional[str] = None
    nocodb_project: Optional[str] = None
    nocodb_table: Optional[str] = None
    
    # Spinweb settings
    spinweb_user: Optional[str] = None
    spinweb_pass: Optional[str] = None
    
    # Matching settings
    excluded_clients: Optional[str] = None
    ai_model: Optional[str] = None
    match_threshold: Optional[float] = None
    match_count: Optional[int] = None
    resume_prompt_template: Optional[str] = None

class SettingsUpdate(BaseModel):
    """Model for updating application settings"""
    openai_api_key: Optional[str] = None
    
    # Database settings
    database_provider: Optional[str] = None
    
    # Supabase settings
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    supabase_resume_table: Optional[str] = None
    
    # PostgreSQL settings
    pg_host: Optional[str] = None
    pg_port: Optional[str] = None
    pg_user: Optional[str] = None
    pg_password: Optional[str] = None
    pg_database: Optional[str] = None
    
    # NocoDB settings
    nocodb_url: Optional[str] = None
    nocodb_token: Optional[str] = None
    nocodb_project: Optional[str] = None
    nocodb_table: Optional[str] = None
    
    # Spinweb settings
    spinweb_user: Optional[str] = None
    spinweb_pass: Optional[str] = None
    
    # Matching settings
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
            
            # Database settings
            database_provider=os.getenv("DATABASE_PROVIDER", "postgres"),
            
            # Supabase settings
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key="*****" if os.getenv("SUPABASE_KEY") else None,
            supabase_resume_table=os.getenv("SUPABASE_RESUME_TABLE", "01_OAS"),
            
            # PostgreSQL settings
            pg_host=os.getenv("PG_HOST", "localhost"),
            pg_port=os.getenv("PG_PORT", "5432"),
            pg_user=os.getenv("PG_USER", "postgres"),
            pg_password="*****" if os.getenv("PG_PASSWORD") else None,
            pg_database=os.getenv("PG_DATABASE", "resumeai"),
            
            # NocoDB settings
            nocodb_url=os.getenv("NOCODB_URL"),
            nocodb_token="*****" if os.getenv("NOCODB_TOKEN") else None,
            nocodb_project=os.getenv("NOCODB_PROJECT"),
            nocodb_table=os.getenv("NOCODB_TABLE"),
            
            # Spinweb settings
            spinweb_user=os.getenv("SPINWEB_USER"),
            spinweb_pass="*****" if os.getenv("SPINWEB_PASS") else None,
            
            # Matching settings
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
            
            # Database settings
            "database_provider": "DATABASE_PROVIDER",
            
            # Supabase settings
            "supabase_url": "SUPABASE_URL",
            "supabase_key": "SUPABASE_KEY",
            "supabase_resume_table": "SUPABASE_RESUME_TABLE",
            
            # PostgreSQL settings
            "pg_host": "PG_HOST",
            "pg_port": "PG_PORT",
            "pg_user": "PG_USER",
            "pg_password": "PG_PASSWORD",
            "pg_database": "PG_DATABASE",
            
            # NocoDB settings
            "nocodb_url": "NOCODB_URL",
            "nocodb_token": "NOCODB_TOKEN",
            "nocodb_project": "NOCODB_PROJECT",
            "nocodb_table": "NOCODB_TABLE",
            
            # Spinweb settings
            "spinweb_user": "SPINWEB_USER",
            "spinweb_pass": "SPINWEB_PASS",
            
            # Matching settings
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

@router.post("/database/switch")
async def switch_database_provider(provider: str):
    """
    Switch database provider.
    
    Args:
        provider: The database provider to switch to ("postgres" or "supabase")
    """
    try:
        logger.info(f"Received request to switch database provider to: {provider}")
        
        if provider not in ["postgres", "supabase"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid provider. Must be 'postgres' or 'supabase'"
            )
            
        # Check if Supabase is available when requested
        if provider == "supabase" and not SUPABASE_AVAILABLE:
            raise HTTPException(
                status_code=400,
                detail="Supabase provider requested but module is not installed. Please install the supabase package."
            )
        
        # Update the provider in memory without checking connections
        # This allows switching even if one provider is currently unavailable
        try:
            old_provider = db_service.provider
            db_service.provider = provider
            logger.info(f"Switched database provider from {old_provider} to {provider}")
            
            # Try to update the environment variable file
            try:
                # Update the provider in the .env file if it exists
                dotenv_path = os.path.join(os.getcwd(), ".env")
                if os.path.exists(dotenv_path):
                    from dotenv import set_key
                    set_key(dotenv_path, "DATABASE_PROVIDER", provider)
                    logger.info(f"Updated DATABASE_PROVIDER in .env file to {provider}")
            except Exception as env_error:
                logger.warning(f"Error updating .env file: {str(env_error)}")
                # Continue even if .env update fails - the in-memory change is what matters
                
            return {"status": "success", "provider": provider}
        except Exception as e:
            logger.error(f"Error changing provider: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error changing provider: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in switch_database_provider: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/database/status")
async def get_database_status():
    """
    Get the status of all configured database providers.
    """
    try:
        # Check connection to all configured providers
        status = db_service.get_connection_status()
        
        # Add current provider
        status["current_provider"] = db_service.provider
        
        # Add resume counts
        counts = {}
        
        # Save current provider
        current_provider = db_service.provider
        
        # Create independent database services for counting - this avoids
        # transaction issues by using completely separate connections
        if status.get("postgres", False):
            try:
                # Create a dedicated service instance for this query
                postgres_service = DatabaseService("postgres")
                counts["postgres"] = postgres_service.count_resumes()
            except Exception as e:
                logger.warning(f"Error counting postgres resumes: {str(e)}")
                counts["postgres"] = None
                
        if status.get("supabase", False):
            try:
                # Create a dedicated service instance for this query
                supabase_service = DatabaseService("supabase")
                counts["supabase"] = supabase_service.count_resumes()
            except Exception as e:
                logger.warning(f"Error counting supabase resumes: {str(e)}")
                counts["supabase"] = None
        
        # Add counts to status
        status["resume_counts"] = counts
        
        return status
    except Exception as e:
        logger.error(f"Error getting database status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting database status: {str(e)}")