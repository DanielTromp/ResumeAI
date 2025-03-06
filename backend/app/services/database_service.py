#!/usr/bin/env python3
"""
Database Service for ResumeAI

This service provides a unified interface to work with different database backends:
- PostgreSQL with pgvector for local storage
- Supabase for cloud storage

Author: Daniel Tromp
Email: drpgmtromp@gmail.com
Version: 0.1.0
Created: 2025-03-06
License: MIT
Repository: https://github.com/DanielTromp/ResumeAI
"""

import os
import logging
import psycopg2
import psycopg2.extras
from typing import List, Dict, Any, Optional, Union, Tuple

# Try to import Supabase, but don't fail if it's not installed
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    # Create dummy class for type hints
    class Client:
        pass
    SUPABASE_AVAILABLE = False
    logging.warning("Supabase module not installed. Supabase support will be disabled.")

from app.config import (
    DATABASE_PROVIDER,
    SUPABASE_URL, SUPABASE_KEY, SUPABASE_RESUME_TABLE,
    PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, PG_DATABASE, POSTGRES_RESUME_TABLE,
    MATCH_THRESHOLD, MATCH_COUNT,
    POSTGRES_MATCH_FUNCTION, SUPABASE_MATCH_FUNCTION
)

# Set up logging
logger = logging.getLogger(__name__)

class DatabaseService:
    """Service to handle different database backends"""
    
    def __init__(self, provider: Optional[str] = None):
        """Initialize the database service with the specified provider"""
        # Set default provider
        requested_provider = provider or DATABASE_PROVIDER
        
        # Enforce PostgreSQL if Supabase is not available
        if requested_provider == "supabase" and not SUPABASE_AVAILABLE:
            logger.warning("Supabase provider requested but module not available. Falling back to PostgreSQL.")
            self.provider = "postgres"
        else:
            self.provider = requested_provider
            
        self._supabase_client = None
        logger.info(f"Initializing DatabaseService with provider: {self.provider}")
    
    @property
    def supabase_client(self) -> Client:
        """Get or create the Supabase client"""
        # Return None if Supabase is not available
        if not SUPABASE_AVAILABLE:
            return None
            
        if self._supabase_client is None and self.provider == "supabase":
            # Check if we have the necessary credentials
            if not SUPABASE_URL or not SUPABASE_KEY:
                logger.warning("❌ Supabase URL or key not configured")
                return None
                
            try:
                self._supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
                logger.info("✅ Connected to Supabase")
            except Exception as e:
                logger.error(f"❌ Error connecting to Supabase: {str(e)}")
                return None
        return self._supabase_client
    
    def get_postgres_connection(self):
        """Get a PostgreSQL connection"""
        try:
            conn = psycopg2.connect(
                host=PG_HOST,
                port=PG_PORT,
                user=PG_USER,
                password=PG_PASSWORD,
                database=PG_DATABASE
            )
            return conn
        except Exception as e:
            logger.error(f"❌ Error connecting to PostgreSQL: {str(e)}")
            raise e
    
    def get_vector_matches(self, embedding: List[float], threshold: float = MATCH_THRESHOLD, 
                           count: int = MATCH_COUNT) -> List[Dict[str, Any]]:
        """
        Get vector matches using the configured database provider
        
        Args:
            embedding: The embedding vector to match against
            threshold: The similarity threshold (0-1)
            count: Maximum number of matches to return
            
        Returns:
            List of matches with name, cv_chunk, and similarity
        """
        if self.provider == "supabase":
            return self._get_supabase_matches(embedding, threshold, count)
        else:
            return self._get_postgres_matches(embedding, threshold, count)
    
    def _get_supabase_matches(self, embedding: List[float], threshold: float, count: int) -> List[Dict[str, Any]]:
        """Get matches from Supabase"""
        client = self.supabase_client
        if client is None:
            logger.error("❌ Supabase client not available")
            return []
            
        try:
            query = client.rpc(
                SUPABASE_MATCH_FUNCTION,
                {
                    "query_embedding": embedding,
                    "match_threshold": threshold,
                    "match_count": count
                }
            ).execute()
            
            if not query.data:
                return []
            
            return query.data
        except Exception as e:
            logger.error(f"❌ Error getting matches from Supabase: {str(e)}")
            return []
    
    def _get_postgres_matches(self, embedding: List[float], threshold: float, count: int) -> List[Dict[str, Any]]:
        """Get matches from PostgreSQL"""
        conn = None
        cursor = None
        try:
            conn = self.get_postgres_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Execute direct query for better reliability
            query = f"""
                SELECT name, cv_chunk, 1 - (embedding <=> %s::vector) AS similarity
                FROM {POSTGRES_RESUME_TABLE}
                WHERE 1 - (embedding <=> %s::vector) > %s
                ORDER BY similarity DESC
                LIMIT %s
            """
            
            cursor.execute(query, (embedding, embedding, threshold, count))
            results = cursor.fetchall()
            
            # Convert psycopg2 DictRow objects to regular dictionaries
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"❌ Error getting matches from PostgreSQL: {str(e)}")
            if conn:
                conn.rollback()  # Always rollback on exception to clear transaction state
            return []
        finally:
            # Always close cursor and connection in finally block
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def add_resume(self, name: str, filename: str, cv_chunk: str, embedding: List[float]) -> bool:
        """
        Add a resume chunk to the database
        
        Args:
            name: The name of the candidate
            filename: The filename of the resume
            cv_chunk: The text chunk from the resume
            embedding: The embedding vector
            
        Returns:
            True if successful, False otherwise
        """
        if self.provider == "supabase":
            return self._add_resume_supabase(name, filename, cv_chunk, embedding)
        else:
            return self._add_resume_postgres(name, filename, cv_chunk, embedding)
    
    def _add_resume_supabase(self, name: str, filename: str, cv_chunk: str, embedding: List[float]) -> bool:
        """Add a resume chunk to Supabase"""
        client = self.supabase_client
        if client is None:
            logger.error("❌ Supabase client not available")
            return False
            
        try:
            client.table(SUPABASE_RESUME_TABLE).insert({
                "name": name,
                "cv_chunk": cv_chunk,
                "embedding": embedding
            }).execute()
            return True
        except Exception as e:
            logger.error(f"❌ Error adding resume to Supabase: {str(e)}")
            return False
    
    def _add_resume_postgres(self, name: str, filename: str, cv_chunk: str, embedding: List[float]) -> bool:
        """Add a resume chunk to PostgreSQL"""
        conn = None
        cursor = None
        try:
            conn = self.get_postgres_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                f"""
                INSERT INTO {POSTGRES_RESUME_TABLE} (name, filename, cv_chunk, embedding) 
                VALUES (%s, %s, %s, %s::vector)
                """,
                (name, filename, cv_chunk, embedding)
            )
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Error adding resume to PostgreSQL: {str(e)}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def delete_resume(self, filename: str) -> bool:
        """
        Delete a resume from the database by filename
        
        Args:
            filename: The filename of the resume to delete
            
        Returns:
            True if successful, False otherwise
        """
        if self.provider == "supabase":
            return self._delete_resume_supabase(filename)
        else:
            return self._delete_resume_postgres(filename)
    
    def _delete_resume_supabase(self, filename: str) -> bool:
        """Delete a resume from Supabase"""
        client = self.supabase_client
        if client is None:
            logger.error("❌ Supabase client not available")
            return False
            
        try:
            # Extract the name from the filename (without extension)
            name = os.path.splitext(filename)[0]
            
            # Delete by name since Supabase table might not have filename field
            client.table(SUPABASE_RESUME_TABLE).delete().eq("name", name).execute()
            return True
        except Exception as e:
            logger.error(f"❌ Error deleting resume from Supabase: {str(e)}")
            return False
    
    def _delete_resume_postgres(self, filename: str) -> bool:
        """Delete a resume from PostgreSQL"""
        conn = None
        cursor = None
        try:
            conn = self.get_postgres_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                f"""
                DELETE FROM {POSTGRES_RESUME_TABLE} 
                WHERE filename = %s
                """,
                (filename,)
            )
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Error deleting resume from PostgreSQL: {str(e)}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def list_resumes(self) -> List[Dict[str, str]]:
        """
        List all resumes in the database
        
        Returns:
            List of resumes with name and filename
        """
        if self.provider == "supabase":
            return self._list_resumes_supabase()
        else:
            return self._list_resumes_postgres()
    
    def _list_resumes_supabase(self) -> List[Dict[str, str]]:
        """List all resumes in Supabase"""
        client = self.supabase_client
        if client is None:
            logger.error("❌ Supabase client not available")
            return []
            
        try:
            response = client.table(SUPABASE_RESUME_TABLE).select("name").execute()
            
            if not response.data:
                return []
            
            # Get unique names
            names = set(item["name"] for item in response.data)
            
            # Format the response
            return [{"name": name, "filename": f"{name}.pdf"} for name in names]
        except Exception as e:
            logger.error(f"❌ Error listing resumes from Supabase: {str(e)}")
            return []
    
    def _list_resumes_postgres(self) -> List[Dict[str, str]]:
        """List all resumes in PostgreSQL"""
        conn = None
        cursor = None
        try:
            conn = self.get_postgres_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            cursor.execute(
                f"""
                SELECT DISTINCT name, filename
                FROM {POSTGRES_RESUME_TABLE}
                ORDER BY name
                """
            )
            
            results = cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"❌ Error listing resumes from PostgreSQL: {str(e)}")
            if conn:
                conn.rollback()
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def count_resumes(self) -> int:
        """Count the number of unique resumes in the database"""
        if self.provider == "supabase":
            return self._count_resumes_supabase()
        else:
            return self._count_resumes_postgres()
    
    def _count_resumes_supabase(self) -> int:
        """Count the number of unique resumes in Supabase"""
        client = self.supabase_client
        if client is None:
            logger.error("❌ Supabase client not available")
            return 0
            
        try:
            response = client.table(SUPABASE_RESUME_TABLE).select("name").execute()
            
            if not response.data:
                return 0
            
            # Get unique names
            names = set(item["name"] for item in response.data)
            return len(names)
        except Exception as e:
            logger.error(f"❌ Error counting resumes in Supabase: {str(e)}")
            return 0
    
    def _count_resumes_postgres(self) -> int:
        """Count the number of unique resumes in PostgreSQL"""
        conn = None
        cursor = None
        try:
            conn = self.get_postgres_connection()
            cursor = conn.cursor()
            
            # First check if table exists
            cursor.execute("SELECT to_regclass('public.resumes')")
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                logger.warning(f"❌ Table {POSTGRES_RESUME_TABLE} does not exist")
                return 0
            
            # Make sure to use the table name from config
            cursor.execute(
                f"""
                SELECT COUNT(DISTINCT name)
                FROM {POSTGRES_RESUME_TABLE}
                """
            )
            
            count = cursor.fetchone()[0]
            logger.info(f"Found {count} unique resumes in PostgreSQL")
            return count
        except Exception as e:
            logger.error(f"❌ Error counting resumes in PostgreSQL: {str(e)}")
            if conn:
                conn.rollback()
            return 0
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def get_connection_status(self) -> Dict[str, bool]:
        """
        Test the connection to the database
        
        Returns:
            Dictionary with status of each provider
        """
        status = {
            "supabase": False,
            "postgres": False
        }
        
        # Test Supabase connection if available
        if SUPABASE_AVAILABLE and SUPABASE_URL and SUPABASE_KEY:
            try:
                # Create a temporary client directly
                temp_client = create_client(SUPABASE_URL, SUPABASE_KEY)
                
                # Test with a simple query
                temp_client.table(SUPABASE_RESUME_TABLE).select("name").limit(1).execute()
                
                # If we get here, connection works
                status["supabase"] = True
                
            except Exception as e:
                logger.warning(f"Supabase connection test failed: {str(e)}")
        else:
            logger.info("Supabase support is not available or not configured")
        
        # Test PostgreSQL connection
        conn = None
        cursor = None
        try:
            conn = self.get_postgres_connection()
            cursor = conn.cursor()
            
            # Check if the resumes table exists - use table name from config
            cursor.execute(f"SELECT to_regclass('public.{POSTGRES_RESUME_TABLE}')")
            table_exists = cursor.fetchone()[0]
            
            if table_exists:
                # Test a simple query with explicit table name from config
                cursor.execute(f"SELECT COUNT(*) FROM {POSTGRES_RESUME_TABLE}")
                cursor.fetchone()
                status["postgres"] = True
                logger.info(f"PostgreSQL connection successful and '{POSTGRES_RESUME_TABLE}' table exists")
            else:
                # Database works but table doesn't exist
                status["postgres"] = True
                logger.warning(f"PostgreSQL connection works but '{POSTGRES_RESUME_TABLE}' table not found")
        except Exception as e:
            logger.warning(f"PostgreSQL connection test failed: {str(e)}")
            if conn:
                conn.rollback()  # Important: rollback on exception
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        
        return status

# Create a global instance
db_service = DatabaseService()