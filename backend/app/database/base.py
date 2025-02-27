"""
Database configuration module

This module provides the database connection functionality with support for
different database backends (NocoDB, SQLite, etc.)

The get_db function should be used as a dependency in FastAPI routes.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Union, Callable, AsyncGenerator
from pydantic import BaseModel
import aiosqlite
from dotenv import load_dotenv

# Import the NocoDB client
from app.components.nocodb_client import NocoDBClient

# Import database initialization
from app.database.init_db import init_db

# Load environment variables
load_dotenv()

# Database configuration
DB_TYPE = os.getenv("DB_TYPE", "sqlite")  # Options: "sqlite", "nocodb"
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "vacancies.db")

# Set up logging
logger = logging.getLogger(__name__)

# Database interface class
class DatabaseInterface:
    """Abstract base class for database operations"""
    
    async def get_all_vacancies(self) -> List[Dict[str, Any]]:
        raise NotImplementedError
    
    async def get_vacancy(self, vacancy_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError
    
    async def create_vacancy(self, vacancy_data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
    
    async def update_vacancy(self, vacancy_id: str, vacancy_data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
    
    async def delete_vacancy(self, vacancy_id: str) -> bool:
        raise NotImplementedError
    
    async def get_all_resumes(self) -> List[Dict[str, Any]]:
        raise NotImplementedError
    
    async def get_resume(self, resume_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

# SQLite implementation
class SQLiteDatabase(DatabaseInterface):
    """SQLite database implementation"""
    
    def __init__(self, db_path: str = SQLITE_DB_PATH):
        self.db_path = db_path
        
    async def _get_connection(self):
        return await aiosqlite.connect(self.db_path)
    
    async def get_all_vacancies(self) -> List[Dict[str, Any]]:
        async with await self._get_connection() as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("SELECT * FROM vacancies ORDER BY geplaatst DESC")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_vacancy(self, vacancy_id: str) -> Optional[Dict[str, Any]]:
        async with await self._get_connection() as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("SELECT * FROM vacancies WHERE id = ?", (vacancy_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def create_vacancy(self, vacancy_data: Dict[str, Any]) -> Dict[str, Any]:
        # Generate a unique ID if not provided
        if 'id' not in vacancy_data:
            import uuid
            vacancy_data['id'] = str(uuid.uuid4())
        
        columns = ", ".join(vacancy_data.keys())
        placeholders = ", ".join(["?" for _ in vacancy_data])
        values = list(vacancy_data.values())
        
        async with await self._get_connection() as conn:
            await conn.execute(
                f"INSERT INTO vacancies ({columns}) VALUES ({placeholders})",
                values
            )
            await conn.commit()
            return vacancy_data
    
    async def update_vacancy(self, vacancy_id: str, vacancy_data: Dict[str, Any]) -> Dict[str, Any]:
        set_clause = ", ".join([f"{key} = ?" for key in vacancy_data.keys()])
        values = list(vacancy_data.values()) + [vacancy_id]
        
        async with await self._get_connection() as conn:
            await conn.execute(
                f"UPDATE vacancies SET {set_clause} WHERE id = ?",
                values
            )
            await conn.commit()
            
            # Get the updated record
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("SELECT * FROM vacancies WHERE id = ?", (vacancy_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def delete_vacancy(self, vacancy_id: str) -> bool:
        async with await self._get_connection() as conn:
            await conn.execute("DELETE FROM vacancies WHERE id = ?", (vacancy_id,))
            await conn.commit()
            return True
    
    async def get_all_resumes(self) -> List[Dict[str, Any]]:
        async with await self._get_connection() as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("SELECT id, name, created_at, updated_at FROM resumes")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_resume(self, resume_id: str) -> Optional[Dict[str, Any]]:
        async with await self._get_connection() as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

# NocoDB implementation
class NocoDBDatabase(DatabaseInterface):
    """NocoDB database implementation"""
    
    def __init__(self):
        self.client = NocoDBClient()
    
    async def get_all_vacancies(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        # The nocodb client is synchronous, so we need to adapt it
        return self.client.get_all_listings(force_refresh=force_refresh)
    
    async def get_vacancy(self, vacancy_id: str) -> Optional[Dict[str, Any]]:
        vacancies = await self.get_all_vacancies()
        for vacancy in vacancies:
            # Convert ID to string for comparison if it's not already a string
            vacancy_id_from_db = vacancy.get("id")
            if not isinstance(vacancy_id_from_db, str):
                vacancy_id_from_db = str(vacancy_id_from_db)
                
            # Compare IDs after ensuring string format
            if vacancy_id_from_db == vacancy_id:
                # Ensure ID is string in returned data
                if not isinstance(vacancy["id"], str):
                    vacancy["id"] = str(vacancy["id"])
                return vacancy
        return None
    
    async def create_vacancy(self, vacancy_data: Dict[str, Any]) -> Dict[str, Any]:
        # The nocodb client expects a URL
        url = vacancy_data.get("URL")
        if not url:
            raise ValueError("URL is required for NocoDB vacancies")
        
        success = self.client.update_record(vacancy_data, url)
        if success:
            return vacancy_data
        else:
            raise Exception("Failed to create vacancy in NocoDB")
    
    async def update_vacancy(self, vacancy_id: str, vacancy_data: Dict[str, Any]) -> Dict[str, Any]:
        # For NocoDB we need the URL, which should be in the vacancy_data
        url = vacancy_data.get("URL")
        if not url:
            # Try to get the URL from the ID, assuming they're the same
            url = vacancy_id
        
        success = self.client.update_record(vacancy_data, url)
        if success:
            return vacancy_data
        else:
            raise Exception("Failed to update vacancy in NocoDB")
    
    async def delete_vacancy(self, vacancy_id: str) -> bool:
        # NocoDB client doesn't have a direct delete method,
        # we would need to implement this in the nocodb_client.py
        # For now, we'll just mark it as deleted
        try:
            vacancy = await self.get_vacancy(vacancy_id)
            if vacancy:
                vacancy["Status"] = "Deleted"
                await self.update_vacancy(vacancy_id, vacancy)
                return True
            return False
        except:
            return False
    
    async def get_all_resumes(self) -> List[Dict[str, Any]]:
        # We need to implement this in the NocoDB client
        # For now, return an empty list
        return []
    
    async def get_resume(self, resume_id: str) -> Optional[Dict[str, Any]]:
        # We need to implement this in the NocoDB client
        # For now, return None
        return None

# Create the database instance based on configuration
def create_db_instance() -> DatabaseInterface:
    if DB_TYPE.lower() == "sqlite":
        return SQLiteDatabase()
    elif DB_TYPE.lower() == "nocodb":
        return NocoDBDatabase()
    else:
        raise ValueError(f"Unsupported database type: {DB_TYPE}")

# Global database instance
db_instance = create_db_instance()

# Database dependency for FastAPI routes
async def get_db() -> AsyncGenerator[DatabaseInterface, None]:
    """Get a database session"""
    yield db_instance