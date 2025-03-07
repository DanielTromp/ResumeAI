#!/usr/bin/env python3
"""
PostgreSQL Database Initialization and Verification

This script initializes the PostgreSQL database for the ResumeAI application:
1. Checks if the database connection is working
2. Creates the pgvector extension if needed
3. Creates the resumes table if it doesn't exist
4. Creates the necessary functions for vector similarity search
5. Optionally adds test data

Author: Daniel Tromp
Email: drpgmtromp@gmail.com
Version: 0.1.0
Created: 2025-03-06
License: MIT
Repository: https://github.com/DanielTromp/ResumeAI
"""

import os
import sys
import argparse
import logging
import json
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# PostgreSQL configuration
PG_HOST = os.getenv("PG_HOST", "localhost")  # Will be "db" in Docker, "localhost" locally
PG_PORT = os.getenv("PG_PORT", "5432")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")
PG_DATABASE = os.getenv("PG_DATABASE", "resumeai")

# Override PG_HOST if it's set to "db" and we're not in Docker
if PG_HOST == "db" and not os.path.exists("/.dockerenv"):
    PG_HOST = "localhost"
    logger.warning(f"Detected non-Docker environment, overriding PG_HOST to {PG_HOST}")

def get_connection():
    """Get a PostgreSQL connection"""
    # Determine if we're running in Docker or local environment
    # Docker setup uses host 'db', local uses 'localhost'
    host = PG_HOST
    logger.info(f"Connecting to PostgreSQL at {host}:{PG_PORT}")
    try:
        conn = psycopg2.connect(
            host=host,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            database=PG_DATABASE
        )
        logger.info("✅ Connected to PostgreSQL")
        return conn
    except Exception as e:
        logger.error(f"❌ Error connecting to PostgreSQL: {str(e)}")
        raise e

def check_database():
    """Check if the database is properly set up"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Test basic connection
        cursor.execute("SELECT 1")
        logger.info("✅ Basic database connection successful")
        
        # Check if pgvector extension is enabled
        cursor.execute("""
            SELECT extname FROM pg_extension WHERE extname = 'vector'
        """)
        pgvector_enabled = cursor.fetchone() is not None
        
        if not pgvector_enabled:
            logger.warning("⚠️ pgvector extension is not enabled")
        else:
            logger.info("✅ pgvector extension is enabled")
        
        # Check if resumes table exists
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'resumes'
        """)
        resumes_table_exists = cursor.fetchone() is not None
        
        if not resumes_table_exists:
            logger.warning("⚠️ resumes table does not exist")
        else:
            logger.info("✅ resumes table exists")
            
            # Check table structure
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'resumes'
            """)
            columns = cursor.fetchall()
            logger.info(f"Resumes table columns: {[col[0] for col in columns]}")
            
            # Check record count
            cursor.execute("SELECT COUNT(*) FROM resumes")
            count = cursor.fetchone()[0]
            logger.info(f"Resume records count: {count}")
            
        # Check if vacancy_statistics table exists
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'vacancy_statistics'
        """)
        stats_table_exists = cursor.fetchone() is not None
        
        if not stats_table_exists:
            logger.warning("⚠️ vacancy_statistics table does not exist")
        else:
            logger.info("✅ vacancy_statistics table exists")
            
            # Check table structure
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'vacancy_statistics'
            """)
            columns = cursor.fetchall()
            logger.info(f"Statistics table columns: {[col[0] for col in columns]}")
            
            # Check record count
            cursor.execute("SELECT COUNT(*) FROM vacancy_statistics")
            count = cursor.fetchone()[0]
            logger.info(f"Statistics records count: {count}")
        
        # Check if vector functions exist
        cursor.execute("""
            SELECT proname, pronargs
            FROM pg_proc 
            WHERE proname = 'match_resumes'
        """)
        functions = cursor.fetchall()
        
        if not functions:
            logger.warning("⚠️ match_resumes function does not exist")
        else:
            logger.info(f"✅ Found {len(functions)} match_resumes functions")
        
        cursor.close()
        conn.close()
        
        return pgvector_enabled and resumes_table_exists and stats_table_exists
    except Exception as e:
        logger.error(f"❌ Error checking database: {str(e)}")
        return False

def initialize_database():
    """Initialize the database with required extensions, tables, and functions"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Create pgvector extension
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
        logger.info("✅ Created pgvector extension")
        
        # Create resumes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS public.resumes (
                id serial PRIMARY KEY,
                name text,
                filename text,
                cv_chunk text,
                embedding vector(1536),
                created_at timestamptz DEFAULT NOW(),
                updated_at timestamptz DEFAULT NOW()
            )
        """)
        logger.info("✅ Created resumes table")
        
        # Create vacancies table with Dutch field names (to match combined_process.py)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS public.vacancies (
                id serial PRIMARY KEY,
                url text UNIQUE,
                functie text,
                klant text,
                functieomschrijving text,
                branche text,
                regio text,
                uren text,
                tarief text,
                status text,
                checked_resumes text,
                top_match integer,
                match_toelichting jsonb,
                geplaatst text,
                sluiting text,
                external_id text,
                model text,
                version text,
                created_at timestamptz DEFAULT NOW(),
                updated_at timestamptz DEFAULT NOW()
            )
        """)
        logger.info("✅ Created vacancies table")
        
        # Create vacancy_statistics table for faster counts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS public.vacancy_statistics (
                id SERIAL PRIMARY KEY,
                status VARCHAR(255) UNIQUE,
                count INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("✅ Created vacancy_statistics table")
        
        # Create vector similarity function
        cursor.execute("""
            CREATE OR REPLACE FUNCTION public.match_resumes(
                query_embedding vector,
                match_threshold double precision,
                match_count integer
            )
            RETURNS TABLE (
                name text,
                cv_chunk text,
                similarity float
            )
            LANGUAGE plpgsql
            AS $$
            BEGIN
              RETURN QUERY
                SELECT
                   resumes.name,
                   resumes.cv_chunk,
                   1 - (resumes.embedding <=> query_embedding) AS similarity
                FROM resumes
                WHERE 1 - (resumes.embedding <=> query_embedding) > match_threshold
                ORDER BY similarity DESC
                LIMIT match_count;
            END;
            $$
        """)
        logger.info("✅ Created match_resumes function")
        
        # Create timestamp update trigger
        cursor.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
               NEW.updated_at = NOW();
               RETURN NEW;
            END;
            $$ LANGUAGE 'plpgsql'
        """)
        
        # Check if trigger exists
        cursor.execute("""
            SELECT tgname FROM pg_trigger
            WHERE tgname = 'update_resumes_updated_at'
        """)
        trigger_exists = cursor.fetchone() is not None
        
        if not trigger_exists:
            cursor.execute("""
                CREATE TRIGGER update_resumes_updated_at
                BEFORE UPDATE ON resumes
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column()
            """)
            logger.info("✅ Created timestamp update trigger")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Database initialization complete")
        return True
    except Exception as e:
        logger.error(f"❌ Error initializing database: {str(e)}")
        return False

def add_test_data():
    """Add test data to the database"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if we already have resume records
        cursor.execute("SELECT COUNT(*) FROM resumes")
        resume_count = cursor.fetchone()[0]
        
        if resume_count == 0:
            # Create dummy embedding (1536 dimensions)
            dummy_embedding = [0.1] * 1536
            
            # Add test record
            cursor.execute(
                """
                INSERT INTO resumes (name, filename, cv_chunk, embedding) 
                VALUES (%s, %s, %s, %s::vector)
                """,
                ("Test User", "test.pdf", "This is a test CV chunk with Python skills and 5 years of experience", dummy_embedding)
            )
            logger.info("✅ Added test resume data to the database")
        else:
            logger.info(f"Database already has {resume_count} resume records, skipping resume test data insertion")
        
        # Check if we already have vacancy records
        try:
            cursor.execute("SELECT COUNT(*) FROM vacancies")
            vacancy_count = cursor.fetchone()[0]
            
            if vacancy_count == 0:
                # Add test vacancy
                cursor.execute(
                    """
                    INSERT INTO vacancies (
                        url, functie, klant, functieomschrijving, branche, regio, 
                        uren, tarief, status, checked_resumes, top_match, match_toelichting,
                        created_at, updated_at
                    ) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    RETURNING id
                    """,
                    (
                        "spinweb.nl/aanvraag/test123",
                        "Test Developer",
                        "Test Client",
                        "This is a test vacancy for a Python developer with 3+ years of experience",
                        "ICT",
                        "Amsterdam",
                        "40 uur",
                        "€80 - €90",
                        "Nieuw",
                        "",
                        0,
                        json.dumps({"test": True})
                    )
                )
                logger.info("✅ Added test vacancy data to the database")
            else:
                logger.info(f"Database already has {vacancy_count} vacancy records, skipping vacancy test data insertion")
        except Exception as vacancy_error:
            logger.error(f"❌ Error adding test vacancy data: {str(vacancy_error)}")
            
        # Initialize vacancy statistics
        try:
            # Check if we have stats records
            cursor.execute("SELECT COUNT(*) FROM vacancy_statistics")
            stats_count = cursor.fetchone()[0]
            
            if stats_count == 0:
                # Initialize statistics by counting vacancies by status
                cursor.execute("""
                INSERT INTO vacancy_statistics (status, count)
                SELECT status, COUNT(*) 
                FROM vacancies 
                GROUP BY status
                """)
                logger.info("✅ Initialized vacancy statistics")
            else:
                logger.info(f"Database already has vacancy statistics, skipping initialization")
        except Exception as stats_error:
            logger.error(f"❌ Error initializing vacancy statistics: {str(stats_error)}")
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ Error adding test data: {str(e)}")
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        return False

def test_vector_search():
    """Test vector similarity search functionality"""
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Create a test embedding
        test_embedding = [0.1] * 1536
        
        # Try different query approaches
        query_methods = [
            {
                "name": "Direct vector casting",
                "query": """
                    SELECT name, cv_chunk, 1 - (embedding <=> %s::vector) AS similarity
                    FROM resumes
                    WHERE 1 - (embedding <=> %s::vector) > 0.5
                    ORDER BY similarity DESC
                    LIMIT 5
                """,
                "params": (test_embedding, test_embedding)
            },
            {
                "name": "Function call",
                "query": """
                    SELECT * FROM match_resumes(%s::vector, 0.5, 5)
                """,
                "params": (test_embedding,)
            }
        ]
        
        success = False
        for method in query_methods:
            try:
                logger.info(f"Testing query method: {method['name']}")
                cursor.execute(method["query"], method["params"])
                results = cursor.fetchall()
                logger.info(f"✅ Query method successful: {method['name']}")
                logger.info(f"Results: {len(results)} matches found")
                success = True
                break
            except Exception as e:
                logger.warning(f"⚠️ Query method failed: {method['name']} - {str(e)}")
                conn.rollback()  # Reset transaction state
        
        cursor.close()
        conn.close()
        return success
    except Exception as e:
        logger.error(f"❌ Error testing vector search: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Initialize and verify the PostgreSQL database")
    parser.add_argument("--check", action="store_true", help="Check if the database is properly set up")
    parser.add_argument("--init", action="store_true", help="Initialize the database")
    parser.add_argument("--test-data", action="store_true", help="Add test data to the database")
    parser.add_argument("--test-search", action="store_true", help="Test vector similarity search")
    
    args = parser.parse_args()
    
    # Default to running all checks if no arguments provided
    if not (args.check or args.init or args.test_data or args.test_search):
        args.check = True
        args.init = True
        args.test_data = True
        args.test_search = True
    
    if args.check:
        logger.info("Checking database setup...")
        database_ok = check_database()
        if not database_ok and args.init:
            logger.info("Database needs initialization...")
        elif not database_ok:
            logger.error("Database is not properly set up. Run with --init to initialize.")
            return 1
    
    if args.init:
        logger.info("Initializing database...")
        if not initialize_database():
            logger.error("Failed to initialize database.")
            return 1
    
    if args.test_data:
        logger.info("Adding test data...")
        if not add_test_data():
            logger.error("Failed to add test data.")
            return 1
    
    if args.test_search:
        logger.info("Testing vector similarity search...")
        if not test_vector_search():
            logger.error("Vector similarity search test failed.")
            return 1
        else:
            logger.info("✅ Vector similarity search test successful")
    
    logger.info("✅ All operations completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())