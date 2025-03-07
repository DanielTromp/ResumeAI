#!/usr/bin/env python3
"""
Quick script to check database statistics
"""

import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# PostgreSQL configuration
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")
PG_DATABASE = os.getenv("PG_DATABASE", "resumeai")

# Override PG_HOST if it's set to "db" and we're not in Docker
if PG_HOST == "db" and not os.path.exists("/.dockerenv"):
    PG_HOST = "localhost"
    print(f"Detected non-Docker environment, overriding PG_HOST to {PG_HOST}")

def main():
    """Main function to check database statistics"""
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            database=PG_DATABASE
        )
        cursor = conn.cursor()
        
        # Check total number of vacancies
        cursor.execute("SELECT COUNT(*) FROM vacancies")
        total_vacancies = cursor.fetchone()[0]
        print(f"Total vacancies in database: {total_vacancies}")
        
        # Check vacancies by status
        cursor.execute("SELECT status, COUNT(*) FROM vacancies GROUP BY status")
        print("\nVacancies by status:")
        for row in cursor.fetchall():
            print(f"- {row[0]}: {row[1]}")
        
        # Check if vacancy_statistics table exists
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'vacancy_statistics'
        """)
        stats_table_exists = cursor.fetchone() is not None
        
        if stats_table_exists:
            print("\nStatistics table:")
            cursor.execute("SELECT status, count FROM vacancy_statistics")
            for row in cursor.fetchall():
                print(f"- {row[0]}: {row[1]}")
            
            # Get total from statistics
            cursor.execute("SELECT SUM(count) FROM vacancy_statistics")
            total_stats = cursor.fetchone()[0]
            print(f"\nTotal from statistics table: {total_stats}")
            
            if total_stats != total_vacancies:
                print(f"⚠️ Statistics are out of sync! Database has {total_vacancies} vacancies, but statistics show {total_stats}")
                print("Run the /rebuild-statistics endpoint to fix this")
        else:
            print("\n⚠️ vacancy_statistics table does not exist")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error checking database: {str(e)}")

if __name__ == "__main__":
    main()