#!/usr/bin/env python3
"""
NocoDB to PostgreSQL Migration Service

This service migrates vacancy data from NocoDB to a PostgreSQL database.
It converts NocoDB record format to a format compatible with PostgreSQL.

Author: Daniel Tromp
Email: drpgmtromp@gmail.com
Version: 0.1.0
Created: 2025-03-06
License: MIT
Repository: https://github.com/DanielTromp/ResumeAI
"""

import os
import logging
import asyncio
import psycopg2
import psycopg2.extras
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Import NocoDB client
from app.components.nocodb_client import NocoDBClient

# Import PostgreSQL configuration
from app.config import (
    PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, PG_DATABASE
)

# Set up logging
logger = logging.getLogger(__name__)

class NocoDBToPostgresService:
    """Service for migrating data from NocoDB to PostgreSQL"""
    
    def __init__(self):
        """Initialize the migration service"""
        self.nocodb_client = NocoDBClient()
        self.pg_table_name = "vacancies"  # PostgreSQL table name
        self.status = {
            "status": "idle",
            "total": 0,
            "migrated": 0,
            "failed": 0,
            "started_at": None,
            "completed_at": None,
            "last_error": None
        }
    
    def get_pg_connection(self):
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
            logger.error(f"Error connecting to PostgreSQL: {str(e)}")
            raise e
    
    def create_vacancies_table(self) -> bool:
        """Create the vacancies table in PostgreSQL if it doesn't exist"""
        conn = None
        cursor = None
        try:
            conn = self.get_pg_connection()
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                )
            """, (self.pg_table_name,))
            
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                # Create the vacancies table
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.pg_table_name} (
                        id SERIAL PRIMARY KEY,
                        external_id TEXT,
                        url TEXT UNIQUE,
                        status TEXT,
                        functie TEXT,
                        klant TEXT,
                        branche TEXT,
                        regio TEXT,
                        uren TEXT,
                        tarief TEXT,
                        geplaatst TIMESTAMP,
                        sluiting TIMESTAMP,
                        functieomschrijving TEXT,
                        top_match INTEGER,
                        match_toelichting TEXT,
                        checked_resumes TEXT,
                        model TEXT,
                        version TEXT,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                
                # Create updated_at trigger
                cursor.execute("""
                    CREATE OR REPLACE FUNCTION update_updated_at_column()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        NEW.updated_at = NOW();
                        RETURN NEW;
                    END;
                    $$ LANGUAGE 'plpgsql'
                """)
                
                cursor.execute(f"""
                    DROP TRIGGER IF EXISTS update_vacancies_updated_at ON {self.pg_table_name};
                    CREATE TRIGGER update_vacancies_updated_at
                    BEFORE UPDATE ON {self.pg_table_name}
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column()
                """)
                
                conn.commit()
                logger.info(f"Created vacancies table in PostgreSQL")
                return True
            else:
                logger.info(f"Vacancies table already exists in PostgreSQL")
                return True
                
        except Exception as e:
            logger.error(f"Error creating vacancies table: {str(e)}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def transform_nocodb_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a NocoDB record to the PostgreSQL format.
        
        This function converts field names and formats date fields appropriately.
        """
        # Create a dictionary for the transformed record
        transformed = {}
        
        # Map field names (lowercase for PostgreSQL)
        field_mapping = {
            "Id": "external_id",
            "id": "external_id",
            "ID": "external_id",
            "URL": "url",
            "Url": "url",
            "Status": "status",
            "Functie": "functie",
            "Klant": "klant",
            "Branche": "branche",
            "Regio": "regio",
            "Uren": "uren",
            "Tarief": "tarief",
            "Geplaatst": "geplaatst",
            "Sluiting": "sluiting",
            "Functieomschrijving": "functieomschrijving",
            "Top Match": "top_match",
            "Match Toelichting": "match_toelichting",
            "Match_Toelichting": "match_toelichting",
            "Checked Resumes": "checked_resumes",
            "Model": "model",
            "Version": "version",
            "Created time": "created_at",
            "Created Time": "created_at",
            "created time": "created_at", 
            "createdat": "created_at",
            "CreatedAt": "created_at", 
            "Updated time": "updated_at",
            "Updated Time": "updated_at",
            "updated time": "updated_at",
            "updatedat": "updated_at",
            "UpdatedAt": "updated_at"
        }
        
        # Log original fields for debugging
        logger.info(f"Original record fields: {list(record.keys())}")
        
        # Convert each field based on mapping
        for key, value in record.items():
            # Skip empty values
            if value is None or value == "":
                continue
                
            # Get the target field name from mapping
            # Clean up key to avoid SQL syntax issues by replacing spaces with underscores
            target_field = field_mapping.get(key, key.lower().replace(" ", "_"))
            
            # Additional safety check: Skip fields that would cause SQL issues
            if target_field in ["createdat", "updatedat"]:
                # Map to proper column names
                if target_field == "createdat":
                    target_field = "created_at"
                    logger.info(f"Remapped field: {key} from '{target_field}' to 'created_at'")
                elif target_field == "updatedat":
                    target_field = "updated_at"
                    logger.info(f"Remapped field: {key} from '{target_field}' to 'updated_at'")
            
            # Handle special transformations
            if target_field == "geplaatst" or target_field == "sluiting":
                # Convert date strings to datetime objects
                if isinstance(value, str):
                    try:
                        # Try different date formats
                        date_formats = [
                            "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", 
                            "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S"
                        ]
                        
                        for fmt in date_formats:
                            try:
                                value = datetime.strptime(value, fmt)
                                break
                            except ValueError:
                                continue
                                
                        # If no format worked, keep as string
                        if isinstance(value, str):
                            logger.warning(f"Could not parse date: {value}, keeping as string")
                    except Exception as e:
                        logger.warning(f"Error converting date {value}: {str(e)}")
            
            # Add to transformed record
            transformed[target_field] = value
            
        return transformed
    
    async def migrate_vacancies(self) -> Dict[str, Any]:
        """
        Migrate all vacancies from NocoDB to PostgreSQL.
        
        Returns a status dictionary with migration results.
        """
        # Update status
        self.status = {
            "status": "running",
            "total": 0,
            "migrated": 0,
            "failed": 0,
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "last_error": None
        }
        
        logger.info("Starting migration from NocoDB to PostgreSQL")
        
        try:
            # Create the vacancies table if needed
            if not self.create_vacancies_table():
                self.status["status"] = "failed"
                self.status["last_error"] = "Failed to create vacancies table"
                return self.status
            
            # Get all records from NocoDB
            nocodb_records = self.nocodb_client.get_all_listings(force_refresh=True)
            
            if not nocodb_records:
                logger.warning("No records found in NocoDB")
                self.status["status"] = "completed"
                self.status["completed_at"] = datetime.now().isoformat()
                return self.status
            
            self.status["total"] = len(nocodb_records)
            logger.info(f"Found {len(nocodb_records)} records in NocoDB")
            
            # Get PostgreSQL connection
            conn = self.get_pg_connection()
            cursor = conn.cursor()
            
            # Process each record
            for record in nocodb_records:
                # Start a fresh transaction for each record
                try:
                    # Transform record
                    transformed_record = self.transform_nocodb_record(record)
                    
                    # Skip if no URL (required unique field)
                    if "url" not in transformed_record or not transformed_record["url"]:
                        logger.warning(f"Skipping record with no URL: {record}")
                        self.status["failed"] += 1
                        continue
                    
                    # Check if record already exists
                    cursor.execute(f"""
                        SELECT id FROM {self.pg_table_name} WHERE url = %s
                    """, (transformed_record["url"],))
                    
                    existing_record = cursor.fetchone()
                    
                    if existing_record:
                        # Update existing record
                        fields = []
                        values = []
                        
                        # Debug: Log the record fields before update
                        logger.info(f"Record fields before update: {list(transformed_record.keys())}")
                        
                        # Filter out problematic fields
                        problematic_fields = ["createdat", "updatedat", "url"]
                        
                        for key, value in transformed_record.items():
                            # Skip URL field for updates and problematic fields
                            if key in problematic_fields:
                                continue
                            
                            fields.append(f"{key} = %s")
                            values.append(value)
                        
                        # Add the URL for the WHERE clause
                        values.append(transformed_record["url"])
                        
                        # Execute the update
                        update_query = f"""
                            UPDATE {self.pg_table_name} 
                            SET {', '.join(fields)}
                            WHERE url = %s
                        """
                        
                        # Debug: Log the query for troubleshooting
                        logger.info(f"Executing update query: {update_query}")
                        
                        cursor.execute(update_query, values)
                        
                    else:
                        # Insert new record
                        fields = list(transformed_record.keys())
                        
                        # Debug: Log field names before insertion
                        logger.info(f"Field names before insertion: {fields}")
                        
                        # Remove any problematic fields that aren't in our table
                        problematic_fields = ["createdat", "updatedat"]
                        fields = [field for field in fields if field not in problematic_fields]
                        
                        placeholders = ["%s"] * len(fields)
                        values = [transformed_record[field] for field in fields]
                        
                        # Execute the insert
                        insert_query = f"""
                            INSERT INTO {self.pg_table_name} ({', '.join(fields)})
                            VALUES ({', '.join(placeholders)})
                        """
                        
                        # Debug: Log the query for troubleshooting
                        logger.info(f"Executing query: {insert_query}")
                        
                        cursor.execute(insert_query, values)
                    
                    # Commit this individual record's transaction
                    conn.commit()
                    
                    # Increment success count
                    self.status["migrated"] += 1
                    
                except Exception as e:
                    logger.error(f"Error migrating record: {str(e)}")
                    self.status["failed"] += 1
                    self.status["last_error"] = str(e)
                    # Rollback the transaction to recover from error state
                    conn.rollback()
                    # Continue with next record
            
            # No need for final commit since we're committing per record
            
            # Close connections
            cursor.close()
            conn.close()
            
            # Update status
            self.status["status"] = "completed"
            self.status["completed_at"] = datetime.now().isoformat()
            
            logger.info(f"Migration completed: {self.status['migrated']} records migrated, {self.status['failed']} failed")
            
            return self.status
            
        except Exception as e:
            logger.error(f"Error in migration process: {str(e)}")
            self.status["status"] = "failed"
            self.status["last_error"] = str(e)
            self.status["completed_at"] = datetime.now().isoformat()
            return self.status
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current migration status"""
        return self.status

# Create global instance
nocodb_to_postgres_service = NocoDBToPostgresService()