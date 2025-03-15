"""
ResumeAI Configuration System

This module provides a centralized configuration system for the ResumeAI application.
It implements a hierarchical configuration approach with the following precedence:
1. Command-line arguments (highest priority)
2. Environment variables
3. Configuration files (.env)
4. Default values (lowest priority)

All configuration values are validated using Pydantic models.
"""

import os
import sys
from typing import List, Optional, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field, ValidationError, field_validator, ConfigDict
from dotenv import load_dotenv

# Determine the application root directory - with Docker compatibility
ROOT_DIR = Path(__file__).parent.parent.parent
# Handle different directory structures in Docker vs local dev
if Path('/app').exists() and Path('/app/app').exists():
    # Docker environment
    print("Detected Docker environment")
    BACKEND_DIR = Path('/app')
    APP_DIR = Path('/app/app')
else:
    # Local development
    print("Detected local development environment")
    BACKEND_DIR = ROOT_DIR / "backend"
    APP_DIR = BACKEND_DIR / "app"

print(f"Root directory: {ROOT_DIR}")
print(f"Backend directory: {BACKEND_DIR}")
print(f"App directory: {APP_DIR}")

# Load environment variables from .env files in order of precedence
# Project root .env (lowest priority)
if (ROOT_DIR / ".env").exists():
    load_dotenv(ROOT_DIR / ".env")

# Backend .env (medium priority)
if (BACKEND_DIR / ".env").exists():
    load_dotenv(BACKEND_DIR / ".env", override=True)

# Local environment overrides (highest priority)
# This allows developers to have their own local configuration
if (BACKEND_DIR / ".env.local").exists():
    load_dotenv(BACKEND_DIR / ".env.local", override=True)


# Configuration models
class DatabaseConfig(BaseModel):
    """Database connection configuration."""
    host: str = Field(default="localhost", description="Database host")
    port: str = Field(default="5432", description="Database port")
    user: str = Field(default="postgres", description="Database user")
    password: str = Field(default="postgres", description="Database password")
    database: str = Field(default="resumeai", description="Database name")
    
    @field_validator('host')
    @classmethod
    def validate_host(cls, v: str) -> str:
        """
        Handle database host automatically based on environment.
        - If in Docker: use 'db' (Docker service name) regardless of config
        - If not in Docker: use 'localhost' if 'db' was specified
        """
        # Running in Docker - always use 'db'
        if os.path.exists("/.dockerenv") and v != "db":
            print(f"Overriding database host from '{v}' to 'db' for Docker environment")
            return "db"
        # Not in Docker but trying to use Docker service name
        elif not os.path.exists("/.dockerenv") and v == "db":
            print(f"Not in Docker environment, overriding database host from 'db' to 'localhost'")
            return "localhost"
        return v
    
    def get_connection_string(self) -> str:
        """Return a formatted connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class OpenAIConfig(BaseModel):
    """OpenAI API configuration."""
    api_key: str = Field(description="OpenAI API key")
    model: str = Field(default="gpt-4o-mini", description="OpenAI model for text generation")
    embedding_model: str = Field(default="text-embedding-ada-002", description="OpenAI model for embeddings")


class SpinwebConfig(BaseModel):
    """Spinweb scraper configuration."""
    username: str = Field(description="Spinweb username")
    password: str = Field(description="Spinweb password")
    login_url: str = Field(default="https://spinweb.nl/inloggen/form", description="Spinweb login URL")
    source_url: str = Field(default="https://spinweb.nl/interim-aanvragen?categories=ICT", 
                            description="URL to scrape for vacancies")
    provider_name: str = Field(default="spinweb.nl", description="Provider name for data source")


class MatchingConfig(BaseModel):
    """Resume matching configuration."""
    threshold: float = Field(default=0.75, ge=0.0, le=1.0, description="Matching threshold (0.0-1.0)")
    count: int = Field(default=20, ge=1, description="Number of matches to return")
    rpc_function_name: str = Field(default="match_resumes", description="PostgreSQL function name for matching")
    excluded_clients: List[str] = Field(default=[], description="List of clients to exclude from matching")
    pdf_folder: str = Field(default="app/resumes/", description="Path to resume PDF files")
    resume_table: str = Field(default="resumes", description="PostgreSQL table name for resumes")


class SchedulerConfig(BaseModel):
    """Scheduler configuration."""
    enabled: bool = Field(default=False, description="Enable the scheduler")
    start_hour: int = Field(default=6, ge=0, le=23, description="Hour to start running (0-23)")
    end_hour: int = Field(default=20, ge=0, le=23, description="Hour to stop running (0-23)")
    interval_minutes: int = Field(default=60, ge=15, description="Interval between runs in minutes")
    days: List[str] = Field(default=["mon", "tue", "wed", "thu", "fri"], 
                            description="Days of the week to run")

    @field_validator('days')
    @classmethod
    def validate_days(cls, v: List[str]) -> List[str]:
        """Validate that days are valid."""
        valid_days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        for day in v:
            if day.lower() not in valid_days:
                raise ValueError(f"Invalid day: {day}. Must be one of {valid_days}")
        return [day.lower() for day in v]


class EmailConfig(BaseModel):
    """Email notification configuration."""
    enabled: bool = Field(default=False, description="Enable email notifications")
    provider: str = Field(default="smtp", description="Email provider (smtp, gmail, mailersend)")
    smtp_host: str = Field(default="smtp.example.com", description="SMTP server hostname")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_use_tls: bool = Field(default=True, description="Use TLS for SMTP connection")
    username: str = Field(default="", description="Email account username")
    password: str = Field(default="", description="Email account password")
    from_email: str = Field(default="resumeai@example.com", description="From email address")
    from_name: str = Field(default="ResumeAI", description="From name")
    recipients: str = Field(default="", description="Comma-separated list of recipient email addresses")
    digest_subject: str = Field(default="ResumeAI - New Processing Results", description="Subject for digest emails")
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate email provider."""
        valid_providers = ["smtp", "gmail", "mailersend"]
        if v.lower() not in valid_providers:
            raise ValueError(f"Invalid provider: {v}. Must be one of {valid_providers}")
        return v.lower()


class AppConfig(BaseModel):
    """Main application configuration."""
    model_config = ConfigDict(extra="allow")
    
    # Database configuration
    database: DatabaseConfig
    
    # OpenAI configuration
    openai: OpenAIConfig
    
    # Spinweb configuration
    spinweb: SpinwebConfig
    
    # Matching configuration
    matching: MatchingConfig
    
    # Scheduler configuration
    scheduler: SchedulerConfig
    
    # Email configuration
    email: EmailConfig = Field(default_factory=EmailConfig)
    
    # Prompt templates
    prompt_template: str


def get_env_or_default(key: str, default: Any = None) -> Any:
    """Get a value from environment variables or return default."""
    return os.environ.get(key, default)


def load_command_line_args() -> Dict[str, Any]:
    """Extract configuration from command-line arguments."""
    # Simple command-line argument parser for configuration overrides
    # Format: --config.section.key=value
    result = {}
    for arg in sys.argv[1:]:
        if arg.startswith("--config."):
            try:
                path, value = arg[9:].split("=", 1)
                
                # Convert value to appropriate type
                if value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
                elif value.isdigit():
                    value = int(value)
                elif value.replace(".", "", 1).isdigit() and value.count(".") == 1:
                    value = float(value)
                
                # Split path into sections
                sections = path.split(".")
                
                # Build nested dictionary
                current = result
                for i, section in enumerate(sections):
                    if i == len(sections) - 1:
                        current[section] = value
                    else:
                        if section not in current:
                            current[section] = {}
                        current = current[section]
            except Exception as e:
                print(f"Error parsing argument {arg}: {e}")
    
    return result


def create_config() -> AppConfig:
    """Create the application configuration from all sources."""
    
    # Load the default prompt template - with smarter path detection
    # Try multiple possible locations for the prompt template
    possible_paths = [
        APP_DIR / "prompt_template.txt",  # Standard path
        Path('/app/app/prompt_template.txt'),  # Docker path
        Path(__file__).parent / "prompt_template.txt",  # Relative to current file
    ]
    
    # Try each path until we find one that exists
    default_prompt_template = None
    for path in possible_paths:
        print(f"Looking for prompt template at: {path}")
        if path.exists():
            try:
                print(f"Found prompt template at: {path}")
                with open(path, "r") as f:
                    default_prompt_template = f.read()
                print(f"Successfully read prompt template (length: {len(default_prompt_template)} chars)")
                break  # Exit the loop once we've found and read the file
            except Exception as e:
                print(f"Error reading prompt template file: {e}")
    
    # If we couldn't find or read the file, use the fallback template
    if default_prompt_template is None:
        print("Using fallback prompt template")
        # Fallback prompt template
        default_prompt_template = """
Je bent een ervaren HR-specialist die helpt bij het evalueren van CV's voor vacatures...
Je taak is om een percentage match te bepalen tussen een CV en een vacature, 
waarbij 0% geen match is en 100% een perfecte match.

**Gewenste kwalificaties en vaardigheden:**
- Vereiste vaardigheden worden uit de functieomschrijving gehaald
- Optionele vaardigheden worden uit de functieomschrijving gehaald
- Ervaring in relevante sector wordt uit de functieomschrijving gehaald
- Vermogen om specifieke taken uit te voeren wordt uit de functieomschrijving gehaald
- Eventuele extra eisen worden uit de functieomschrijving gehaald

**Beoordelingscriteria:**
1. **Functieniveau vergelijking (ZEER BELANGRIJK):**
   - Vergelijk het niveau van de huidige functie met de vacature
   - Een stap terug in functieniveau is NIET wenselijk
   - Geef een negatief advies als de vacature een duidelijke stap terug is
   - Weeg dit zwaar mee in het matchpercentage
2. **Relevantie van werkervaring:** Hoe goed sluit de werkervaring van de kandidaat aan bij de functie? 
   - Is de ervaring **strategisch, operationeel of hands-on**?
3. **Vaardigheden match:** Heeft de kandidaat de vereiste vaardigheden en hoe sterk zijn ze aanwezig?
4. **Praktische inzetbaarheid:** Is de kandidaat direct inzetbaar of is er een leercurve?
5. **Risico's:** Zijn er risico's door gebrek aan specifieke ervaring, werkstijl of een te groot verschil met de functie?

**Uitvoer:**
- **Matchpercentage (0-100%)** op basis van hoe goed de kandidaat past bij de functie.
  Als de vacature een stap terug is in functieniveau, geef dan maximaal 40% match.
- **Sterke punten** van de kandidaat.
- **Zwakke punten** en aandachtspunten.
- **Eindoordeel** of de kandidaat geschikt is, met argumentatie.
  Begin het eindoordeel met een duidelijke analyse van het functieniveau verschil.

Geef ook een analyse van drie sterke punten en drie zwakke punten van de kandidaat in relatie tot de vacature.
Sluit af met een kort, helder eindoordeel over de geschiktheid van de kandidaat.

Vacature:
{vacancy_text}

CV:
{cv_text}

Je analyse moet de volgende structuur hebben (in het Nederlands):
```json
{{
  "name": "{name}",
  "percentage": [0-100],
  "sterke_punten": [
    "Punt 1",
    "Punt 2",
    "Punt 3"
  ],
  "zwakke_punten": [
    "Punt 1",
    "Punt 2",
    "Punt 3"
  ],
  "eindoordeel": "Je beknopte analyse en conclusie."
}}
```
Let op: je output moet een geldig JSON-object zijn, niet alleen de waarden.
"""

    # Log which prompt template we're using
    print(f"Using prompt template with first line: {default_prompt_template.splitlines()[0]}")
    
    # Base configuration from defaults and environment variables
    config_dict = {
        "database": {
            "host": get_env_or_default("PG_HOST", "localhost"),
            "port": get_env_or_default("PG_PORT", "5432"),
            "user": get_env_or_default("PG_USER", "postgres"),
            "password": get_env_or_default("PG_PASSWORD", "postgres"),
            "database": get_env_or_default("PG_DATABASE", "resumeai")
        },
        "openai": {
            "api_key": get_env_or_default("OPENAI_API_KEY", ""),
            "model": get_env_or_default("AI_MODEL", "gpt-4o-mini"),
            "embedding_model": get_env_or_default("EMBEDDING_MODEL", "text-embedding-ada-002")
        },
        "spinweb": {
            "username": get_env_or_default("SPINWEB_USER", ""),
            "password": get_env_or_default("SPINWEB_PASS", ""),
            "login_url": get_env_or_default("SPINWEB_LOGIN", "https://spinweb.nl/inloggen/form"),
            "source_url": get_env_or_default("SOURCE_URL", "https://spinweb.nl/interim-aanvragen?categories=ICT"),
            "provider_name": get_env_or_default("PROVIDER_NAME", "spinweb.nl")
        },
        "matching": {
            "threshold": float(get_env_or_default("MATCH_THRESHOLD", "0.75")),
            "count": int(get_env_or_default("MATCH_COUNT", "20")),
            "rpc_function_name": get_env_or_default("RESUME_RPC_FUNCTION_NAME", "match_resumes"),
            "excluded_clients": get_env_or_default("EXCLUDED_CLIENTS", "").split(",") if get_env_or_default("EXCLUDED_CLIENTS") else [],
            "pdf_folder": get_env_or_default("PDF_FOLDER", "app/resumes/"),
            "resume_table": get_env_or_default("POSTGRES_RESUME_TABLE", "resumes")
        },
        "scheduler": {
            "enabled": get_env_or_default("SCHEDULER_ENABLED", "false").lower() == "true",
            "start_hour": int(get_env_or_default("SCHEDULER_START_HOUR", "6")),
            "end_hour": int(get_env_or_default("SCHEDULER_END_HOUR", "20")),
            "interval_minutes": int(get_env_or_default("SCHEDULER_INTERVAL_MINUTES", "60")),
            "days": get_env_or_default("SCHEDULER_DAYS", "mon,tue,wed,thu,fri").lower().split(",")
        },
        "email": {
            "enabled": get_env_or_default("EMAIL_ENABLED", "false").lower() == "true",
            "provider": get_env_or_default("EMAIL_PROVIDER", "smtp"),
            "smtp_host": get_env_or_default("EMAIL_SMTP_HOST", "smtp.example.com"),
            "smtp_port": int(get_env_or_default("EMAIL_SMTP_PORT", "587")),
            "smtp_use_tls": get_env_or_default("EMAIL_SMTP_USE_TLS", "true").lower() == "true",
            "username": get_env_or_default("EMAIL_USERNAME", ""),
            "password": get_env_or_default("EMAIL_PASSWORD", ""),
            "from_email": get_env_or_default("EMAIL_FROM_EMAIL", "resumeai@example.com"),
            "from_name": get_env_or_default("EMAIL_FROM_NAME", "ResumeAI"),
            "recipients": get_env_or_default("EMAIL_RECIPIENTS", ""),
            "digest_subject": get_env_or_default("EMAIL_DIGEST_SUBJECT", "ResumeAI - New Processing Results"),
        },
        "prompt_template": get_env_or_default("RESUME_PROMPT_TEMPLATE", default_prompt_template)
    }
    
    # Override with command-line arguments (highest priority)
    cmd_args = load_command_line_args()
    
    def deep_update(d, u):
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                deep_update(d[k], v)
            else:
                d[k] = v
    
    deep_update(config_dict, cmd_args)
    
    # Create and validate the configuration
    try:
        return AppConfig(**config_dict)
    except ValidationError as e:
        print(f"Configuration validation error: {e}")
        sys.exit(1)


# Get frontend URL from environment variable
FRONTEND_URL = get_env_or_default("FRONTEND_URL", "http://localhost:3000")

# Create the configuration
config = create_config()

# Export individual configurations for backward compatibility
# This allows existing code to import specific configurations without changes
database_config = config.database
openai_config = config.openai
spinweb_config = config.spinweb
matching_config = config.matching
scheduler_config = config.scheduler
email_config = config.email

# Export individual variables for backward compatibility
# This allows existing code to import specific variables without changes
OPENAI_API_KEY = openai_config.api_key
AI_MODEL = openai_config.model
EMBEDDING_MODEL = openai_config.embedding_model

PG_HOST = database_config.host
PG_PORT = database_config.port
PG_USER = database_config.user
PG_PASSWORD = database_config.password
PG_DATABASE = database_config.database
DATABASE_URL = database_config.get_connection_string()

# Spinweb config - ensure keys match the names used in combined_process.py
URL1_SPINWEB_USER = spinweb_config.username
URL1_SPINWEB_PASS = spinweb_config.password
URL1_LOGIN_URL = spinweb_config.login_url
URL1_SOURCE = spinweb_config.source_url
URL1_PROVIDER_NAME = spinweb_config.provider_name

MATCH_THRESHOLD = matching_config.threshold
MATCH_COUNT = matching_config.count
RESUME_RPC_FUNCTION_NAME = matching_config.rpc_function_name
EXCLUDED_CLIENTS = matching_config.excluded_clients
PDF_FOLDER = matching_config.pdf_folder
POSTGRES_RESUME_TABLE = matching_config.resume_table

# Email config
EMAIL_ENABLED = email_config.enabled
EMAIL_PROVIDER = email_config.provider
EMAIL_SMTP_HOST = email_config.smtp_host
EMAIL_SMTP_PORT = email_config.smtp_port
EMAIL_SMTP_USE_TLS = email_config.smtp_use_tls
EMAIL_USERNAME = email_config.username
EMAIL_PASSWORD = email_config.password
EMAIL_FROM_EMAIL = email_config.from_email
EMAIL_FROM_NAME = email_config.from_name
EMAIL_RECIPIENTS = email_config.recipients
EMAIL_DIGEST_SUBJECT = email_config.digest_subject

PROMPT_TEMPLATE = config.prompt_template

# If this module is run directly, print the configuration
if __name__ == "__main__":
    import json
    from pydantic import BaseModel
    
    # Custom JSON encoder for Pydantic models
    class PydanticEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, BaseModel):
                return obj.model_dump()
            return super().default(obj)
    
    # Print the configuration in JSON format
    print(json.dumps(config.model_dump(), indent=2, cls=PydanticEncoder))