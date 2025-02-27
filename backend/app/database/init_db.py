"""
Database initialization module

This module handles the initialization of the database 
(creating tables, etc.) for SQLite backend.
"""

import os
import logging
import aiosqlite
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_TYPE = os.getenv("DB_TYPE", "sqlite")
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "vacancies.db")

# Set up logging
logger = logging.getLogger(__name__)

async def init_sqlite_db():
    """Initialize the SQLite database tables if they don't exist"""
    logger.info(f"Initializing SQLite database at {SQLITE_DB_PATH}")
    
    async with aiosqlite.connect(SQLITE_DB_PATH) as conn:
        # Create vacancies table
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS vacancies (
            id TEXT PRIMARY KEY,
            url TEXT UNIQUE,
            status TEXT,
            functie TEXT,
            klant TEXT,
            branche TEXT,
            regio TEXT,
            uren TEXT,
            tarief TEXT,
            geplaatst TEXT,
            sluiting TEXT,
            functieomschrijving TEXT,
            top_match INTEGER,
            match_toelichting TEXT,
            checked_resumes TEXT,
            model TEXT,
            version TEXT
        )
        ''')
        
        # Create resumes table
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS resumes (
            id TEXT PRIMARY KEY,
            name TEXT,
            content TEXT,
            embedding TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        ''')
        
        await conn.commit()
        logger.info("SQLite database initialization completed")

async def init_db():
    """Initialize the appropriate database based on configuration"""
    if DB_TYPE.lower() == "sqlite":
        await init_sqlite_db()
    elif DB_TYPE.lower() == "nocodb":
        # NocoDB doesn't require initialization
        logger.info("Using NocoDB backend - no initialization required")
    else:
        logger.warning(f"Unsupported database type: {DB_TYPE}")