"""
Database configuration module

This module provides the database connection functionality with support for
different database backends (NocoDB, SQLite, etc.)

The get_db function should be used as a dependency in FastAPI routes.
"""

import os
import json
import logging
import datetime
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
    
    async def get_all_vacancies(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
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
    
    async def get_all_vacancies(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
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
        # We pass the force_refresh parameter to bypass caching when needed
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

# PostgreSQL implementation
class PostgreSQLDatabase(DatabaseInterface):
    """PostgreSQL database implementation"""
    
    def __init__(self):
        """Initialize PostgreSQL database connection"""
        self.pg_host = os.getenv("PG_HOST", "localhost")
        self.pg_port = os.getenv("PG_PORT", "5432")
        self.pg_user = os.getenv("PG_USER", "postgres")
        self.pg_password = os.getenv("PG_PASSWORD", "postgres")
        self.pg_database = os.getenv("PG_DATABASE", "resumeai")
        self.table_name = "vacancies"
        
        try:
            # Try to import asyncpg
            import asyncpg
            self.asyncpg_available = True
        except ImportError:
            # Fall back to psycopg2 if asyncpg is not available
            self.asyncpg_available = False
            import psycopg2
            import psycopg2.extras
            
        logger.info(f"Using PostgreSQL backend at {self.pg_host}:{self.pg_port}")
    
    async def get_connection(self):
        """Get a PostgreSQL connection"""
        if self.asyncpg_available:
            import asyncpg
            conn = await asyncpg.connect(
                host=self.pg_host,
                port=self.pg_port,
                user=self.pg_user,
                password=self.pg_password,
                database=self.pg_database
            )
            return conn
        else:
            # Using psycopg2 with a connection pool would be better
            import psycopg2
            import psycopg2.extras
            conn = psycopg2.connect(
                host=self.pg_host,
                port=self.pg_port,
                user=self.pg_user,
                password=self.pg_password,
                database=self.pg_database
            )
            return conn
    
    async def get_all_vacancies(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Get all vacancies from PostgreSQL"""
        logger.info("PostgreSQL get_all_vacancies called")
        try:
            # We need to use a synchronous driver for now in this async function
            import psycopg2
            import psycopg2.extras
            
            # Connect directly using psycopg2
            conn = psycopg2.connect(
                host=self.pg_host,
                port=self.pg_port,
                user=self.pg_user,
                password=self.pg_password,
                database=self.pg_database
            )
            
            # Create a cursor that returns dictionaries
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Execute the query - note the column names are case-sensitive in PostgreSQL
            try:
                # First try with lowercase field names (PostgreSQL convention)
                cursor.execute(f"SELECT * FROM {self.table_name} ORDER BY created_at DESC")
            except Exception as e:
                # If that fails, try without ordering
                logger.warning(f"Error ordering by created_at, falling back to unordered query: {str(e)}")
                cursor.execute(f"SELECT * FROM {self.table_name}")
            
            # Fetch all results
            rows = cursor.fetchall()
            
            # Convert rows to a list of dictionaries and normalize field names
            results = []
            for row in rows:
                # Convert row to a regular dictionary (as it's a RealDictRow)
                result = dict(row)
                
                # Map PostgreSQL field names to expected frontend/model field names
                field_mapping = {
                    'url': 'URL',
                    'status': 'Status',
                    'functie': 'Functie',
                    'klant': 'Klant',
                    'branche': 'Branche', 
                    'regio': 'Regio',
                    'uren': 'Uren',
                    'tarief': 'Tarief',
                    'geplaatst': 'Geplaatst',
                    'sluiting': 'Sluiting',
                    'functieomschrijving': 'Functieomschrijving',
                    'top_match': 'Top_Match',
                    'match_toelichting': 'Match_Toelichting',
                    'checked_resumes': 'Checked_resumes',
                    'external_id': 'Id'
                }
                
                # Create a new normalized result
                normalized = {}
                
                # Process all fields
                for key, value in result.items():
                    # Check if binary data needs conversion
                    if isinstance(value, (bytes, bytearray)):
                        value = value.decode('utf-8')
                        
                    # Map PostgreSQL field names to expected model field names
                    if key in field_mapping:
                        normalized[field_mapping[key]] = value
                    else:
                        normalized[key] = value
                
                # Use 'id' as is, or external_id as fallback for 'id'
                if 'id' in normalized:
                    if 'Id' not in normalized:
                        normalized['Id'] = str(normalized['id']) 
                elif 'external_id' in result:
                    normalized['id'] = result['external_id']
                
                # Ensure URL field is always present
                if 'URL' not in normalized and 'url' in result:
                    normalized['URL'] = result['url']
                    
                results.append(normalized)
            
            # Close cursor and connection
            cursor.close()
            conn.close()
            
            logger.info(f"Retrieved {len(results)} vacancies from PostgreSQL")
            return results
            
        except Exception as e:
            logger.error(f"Error fetching vacancies from PostgreSQL: {str(e)}")
            return []
    
    async def get_vacancy(self, vacancy_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific vacancy by ID"""
        logger.info(f"PostgreSQL get_vacancy called for ID {vacancy_id}")
        try:
            import psycopg2
            import psycopg2.extras
            
            conn = psycopg2.connect(
                host=self.pg_host,
                port=self.pg_port,
                user=self.pg_user,
                password=self.pg_password,
                database=self.pg_database
            )
            
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE id = %s OR external_id = %s", 
                          (vacancy_id, vacancy_id))
            
            row = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if row:
                # Convert to regular dictionary
                result = dict(row)
                
                # Map PostgreSQL field names to expected frontend/model field names
                field_mapping = {
                    'url': 'URL',
                    'status': 'Status',
                    'functie': 'Functie',
                    'klant': 'Klant',
                    'branche': 'Branche', 
                    'regio': 'Regio',
                    'uren': 'Uren',
                    'tarief': 'Tarief',
                    'geplaatst': 'Geplaatst',
                    'sluiting': 'Sluiting',
                    'functieomschrijving': 'Functieomschrijving',
                    'top_match': 'Top_Match',
                    'match_toelichting': 'Match_Toelichting',
                    'checked_resumes': 'Checked_resumes',
                    'external_id': 'Id'
                }
                
                # Create a new normalized result
                normalized = {}
                
                # Process all fields
                for key, value in result.items():
                    # Check if binary data needs conversion
                    if isinstance(value, (bytes, bytearray)):
                        value = value.decode('utf-8')
                        
                    # Map PostgreSQL field names to expected model field names
                    if key in field_mapping:
                        normalized[field_mapping[key]] = value
                    else:
                        normalized[key] = value
                
                # Use 'id' as is, or external_id as fallback for 'id'
                if 'id' in normalized:
                    if 'Id' not in normalized:
                        normalized['Id'] = str(normalized['id']) 
                elif 'external_id' in result:
                    normalized['id'] = result['external_id']
                
                # Ensure URL field is always present
                if 'URL' not in normalized and 'url' in result:
                    normalized['URL'] = result['url']
                    
                return normalized
            return None
            
        except Exception as e:
            logger.error(f"Error fetching vacancy {vacancy_id} from PostgreSQL: {str(e)}")
            return None
    
    async def create_vacancy(self, vacancy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new vacancy"""
        logger.info("PostgreSQL create_vacancy called")
        try:
            import psycopg2
            import psycopg2.extras
            
            conn = psycopg2.connect(
                host=self.pg_host,
                port=self.pg_port,
                user=self.pg_user,
                password=self.pg_password,
                database=self.pg_database
            )
            
            cursor = conn.cursor()
            
            # Prepare the fields and values
            fields = list(vacancy_data.keys())
            placeholders = ["%s"] * len(fields)
            values = [vacancy_data[field] for field in fields]
            
            # Execute the insert
            query = f"INSERT INTO {self.table_name} ({', '.join(fields)}) VALUES ({', '.join(placeholders)}) RETURNING id"
            cursor.execute(query, values)
            
            # Get the inserted ID
            inserted_id = cursor.fetchone()[0]
            vacancy_data['id'] = inserted_id
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return vacancy_data
            
        except Exception as e:
            logger.error(f"Error creating vacancy in PostgreSQL: {str(e)}")
            return vacancy_data
    
    async def update_vacancy(self, vacancy_id: str, vacancy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing vacancy"""
        logger.info(f"PostgreSQL update_vacancy called for ID {vacancy_id}")
        try:
            import psycopg2
            import psycopg2.extras
            
            conn = psycopg2.connect(
                host=self.pg_host,
                port=self.pg_port,
                user=self.pg_user,
                password=self.pg_password,
                database=self.pg_database
            )
            
            cursor = conn.cursor()
            
            # Prepare the SET clause and values
            set_clause = []
            values = []
            
            for key, value in vacancy_data.items():
                # Skip the ID field for the SET clause
                if key != 'id' and key != 'external_id':
                    set_clause.append(f"{key} = %s")
                    values.append(value)
            
            # Add the WHERE clause value
            values.append(vacancy_id)
            
            # Execute the update
            query = f"UPDATE {self.table_name} SET {', '.join(set_clause)} WHERE id = %s OR external_id = %s"
            cursor.execute(query, values + [vacancy_id])  # Add vacancy_id twice for both conditions
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return vacancy_data
            
        except Exception as e:
            logger.error(f"Error updating vacancy {vacancy_id} in PostgreSQL: {str(e)}")
            return vacancy_data
    
    async def delete_vacancy(self, vacancy_id: str) -> bool:
        """Delete a vacancy"""
        logger.info(f"PostgreSQL delete_vacancy called for ID {vacancy_id}")
        try:
            import psycopg2
            
            conn = psycopg2.connect(
                host=self.pg_host,
                port=self.pg_port,
                user=self.pg_user,
                password=self.pg_password,
                database=self.pg_database
            )
            
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {self.table_name} WHERE id = %s OR external_id = %s", 
                          (vacancy_id, vacancy_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting vacancy {vacancy_id} from PostgreSQL: {str(e)}")
            return False
    
    async def get_all_resumes(self) -> List[Dict[str, Any]]:
        """Get all resumes"""
        logger.info("PostgreSQL get_all_resumes called")
        try:
            import psycopg2
            import psycopg2.extras
            
            conn = psycopg2.connect(
                host=self.pg_host,
                port=self.pg_port,
                user=self.pg_user,
                password=self.pg_password,
                database=self.pg_database
            )
            
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(f"SELECT id, name, created_at, updated_at FROM resumes ORDER BY created_at DESC")
            
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append(dict(row))
            
            cursor.close()
            conn.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching resumes from PostgreSQL: {str(e)}")
            return []
    
    async def get_resume(self, resume_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific resume by ID"""
        logger.info(f"PostgreSQL get_resume called for ID {resume_id}")
        try:
            import psycopg2
            import psycopg2.extras
            
            conn = psycopg2.connect(
                host=self.pg_host,
                port=self.pg_port,
                user=self.pg_user,
                password=self.pg_password,
                database=self.pg_database
            )
            
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(f"SELECT * FROM resumes WHERE id = %s", (resume_id,))
            
            row = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"Error fetching resume {resume_id} from PostgreSQL: {str(e)}")
            return None

# Create the database instance based on configuration
def create_db_instance() -> DatabaseInterface:
    if DB_TYPE.lower() == "sqlite":
        return SQLiteDatabase()
    elif DB_TYPE.lower() == "nocodb":
        return NocoDBDatabase()
    elif DB_TYPE.lower() == "postgres":
        return PostgreSQLDatabase()
    else:
        raise ValueError(f"Unsupported database type: {DB_TYPE}")

# Global database instance
db_instance = create_db_instance()

# Database dependency for FastAPI routes
async def get_db() -> AsyncGenerator[DatabaseInterface, None]:
    """Get a database session"""
    yield db_instance