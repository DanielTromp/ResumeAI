"""
Settings API Router

This module provides API endpoints for managing application settings.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Dict, Any, Optional
import logging
import os
import sys
from datetime import datetime
from pydantic import BaseModel
from dotenv import load_dotenv

from app.db_init import get_connection

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Import services
from app.services.database_service import db_service, DatabaseService
from app.services.email_service import email_service

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
    
    # Email settings
    email_enabled: Optional[bool] = None
    email_provider: Optional[str] = None
    email_smtp_host: Optional[str] = None
    email_smtp_port: Optional[int] = None
    email_smtp_use_tls: Optional[bool] = None
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    email_from_email: Optional[str] = None
    email_from_name: Optional[str] = None
    email_recipients: Optional[str] = None
    email_digest_subject: Optional[str] = None

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
    
    # Email settings
    email_enabled: Optional[bool] = None
    email_provider: Optional[str] = None
    email_smtp_host: Optional[str] = None
    email_smtp_port: Optional[int] = None
    email_smtp_use_tls: Optional[bool] = None
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    email_from_email: Optional[str] = None
    email_from_name: Optional[str] = None
    email_recipients: Optional[str] = None
    email_digest_subject: Optional[str] = None

@router.get("/", response_model=Settings)
@router.get("", response_model=Settings)  # Add route without trailing slash
async def get_settings():
    """
    Get application settings.
    
    Note: For security reasons, sensitive values are redacted.
    """
    try:
        # Load environment variables
        load_dotenv()
        
        # Import PROMPT_TEMPLATE from config
        from app.config import PROMPT_TEMPLATE
        
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
            resume_prompt_template=PROMPT_TEMPLATE,
            
            # Scheduler settings
            scheduler_enabled=os.getenv("SCHEDULER_ENABLED", "false").lower() == "true",
            scheduler_start_hour=int(os.getenv("SCHEDULER_START_HOUR", "6")),
            scheduler_end_hour=int(os.getenv("SCHEDULER_END_HOUR", "20")),
            scheduler_interval_minutes=int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "60")),
            scheduler_days=os.getenv("SCHEDULER_DAYS", "mon,tue,wed,thu,fri"),
            
            # Email settings
            email_enabled=os.getenv("EMAIL_ENABLED", "false").lower() == "true",
            email_provider=os.getenv("EMAIL_PROVIDER", "smtp"),
            email_smtp_host=os.getenv("EMAIL_SMTP_HOST", "smtp.example.com"),
            email_smtp_port=int(os.getenv("EMAIL_SMTP_PORT", "587")),
            email_smtp_use_tls=os.getenv("EMAIL_SMTP_USE_TLS", "true").lower() == "true",
            email_username=os.getenv("EMAIL_USERNAME", ""),
            email_password="*****" if os.getenv("EMAIL_PASSWORD") else None,
            email_from_email=os.getenv("EMAIL_FROM_EMAIL", "resumeai@example.com"),
            email_from_name=os.getenv("EMAIL_FROM_NAME", "ResumeAI"),
            email_recipients=os.getenv("EMAIL_RECIPIENTS", ""),
            email_digest_subject=os.getenv("EMAIL_DIGEST_SUBJECT", "ResumeAI - New Processing Results")
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
            "scheduler_days": {"env_key": "SCHEDULER_DAYS", "is_masked": False},
            
            # Email settings
            "email_enabled": {"env_key": "EMAIL_ENABLED", "is_masked": False},
            "email_provider": {"env_key": "EMAIL_PROVIDER", "is_masked": False},
            "email_smtp_host": {"env_key": "EMAIL_SMTP_HOST", "is_masked": False},
            "email_smtp_port": {"env_key": "EMAIL_SMTP_PORT", "is_masked": False},
            "email_smtp_use_tls": {"env_key": "EMAIL_SMTP_USE_TLS", "is_masked": False},
            "email_username": {"env_key": "EMAIL_USERNAME", "is_masked": False},
            "email_password": {"env_key": "EMAIL_PASSWORD", "is_masked": True},
            "email_from_email": {"env_key": "EMAIL_FROM_EMAIL", "is_masked": False},
            "email_from_name": {"env_key": "EMAIL_FROM_NAME", "is_masked": False},
            "email_recipients": {"env_key": "EMAIL_RECIPIENTS", "is_masked": False},
            "email_digest_subject": {"env_key": "EMAIL_DIGEST_SUBJECT", "is_masked": False}
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
        
        # Handle the prompt template specially - write it to the prompt_template.txt file
        if "resume_prompt_template" in filtered_updates:
            prompt_template = filtered_updates.pop("resume_prompt_template")
            try:
                # Write the prompt template to the file
                from pathlib import Path
                # Get the correct path for Docker or local environment
                if Path('/app').exists() and Path('/app/app').exists():
                    # Docker environment
                    prompt_template_path = Path('/app/app/prompt_template.txt')
                else:
                    # Local development
                    prompt_template_path = Path(__file__).parent.parent / "prompt_template.txt"
                
                print(f"Writing prompt template to: {prompt_template_path}")
                with open(prompt_template_path, "w") as f:
                    f.write(prompt_template)
                
                # Force the configuration to reload the prompt template
                from app.config import config
                import importlib
                importlib.reload(sys.modules['app.config'])
                
                logger.info(f"Updated prompt template at {prompt_template_path}")
            except Exception as e:
                logger.error(f"Error updating prompt template file: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error updating prompt template file: {str(e)}")
        
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
        
        
class TestEmailRequest(BaseModel):
    """Model for test email request"""
    recipient: Optional[str] = None
    subject: Optional[str] = None


@router.post("/email/test")
async def send_test_email(request: TestEmailRequest):
    """
    Send a test email to verify email settings.
    
    Sends a simple test email using the current email settings.
    If recipient is provided, it will override the configured recipients.
    """
    try:
        # Prepare email data
        subject = request.subject or "ResumeAI Test Email"
        recipients = None
        if request.recipient:
            recipients = [request.recipient]
            
        # Create HTML and text content
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                h1 {{ color: #2c3e50; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #777; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>ResumeAI Test Email</h1>
                <p>This is a test email from the ResumeAI system.</p>
                <p>If you are receiving this email, your email configuration is working correctly!</p>
                <p>Current configuration:</p>
                <ul>
                    <li>Provider: {email_service.config.provider}</li>
                    <li>From: {email_service.config.from_name} &lt;{email_service.config.from_email}&gt;</li>
                    <li>SMTP Host: {email_service.config.smtp_host}</li>
                </ul>
                <div class="footer">
                    <p>This is an automated test message from ResumeAI.</p>
                    <p>Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        ResumeAI Test Email
        ===================
        
        This is a test email from the ResumeAI system.
        
        If you are receiving this email, your email configuration is working correctly!
        
        Current configuration:
        - Provider: {email_service.config.provider}
        - From: {email_service.config.from_name} <{email_service.config.from_email}>
        - SMTP Host: {email_service.config.smtp_host}
        
        This is an automated test message from ResumeAI.
        Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """
        
        # Send email
        success = email_service.send_email(
            subject=subject,
            recipients=recipients,
            html_content=html_content,
            text_content=text_content
        )
        
        if success:
            return {"status": "success", "message": "Test email sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send test email")
            
    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending test email: {str(e)}")