"""
PostgreSQL Database Interface

Provides direct interface to PostgreSQL database operations.
"""

import os
import json
import logging
import datetime
import psycopg2
import psycopg2.extras
from typing import List, Dict, Any, Optional, Tuple

from app.config import (
    PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, PG_DATABASE
)

logger = logging.getLogger(__name__)

def get_connection():
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

def get_all_vacancies(status: Optional[str] = None, skip: int = 0, limit: int = 10000) -> List[Dict[str, Any]]:
    """Get all vacancies from PostgreSQL with filtering and pagination"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Build the base query and conditions
        base_query = "FROM vacancies"
        where_clause = ""
        params = []
        
        if status:
            # Make sure we handle case sensitivity correctly
            where_clause = " WHERE LOWER(status) = LOWER(%s)"
            params.append(status)
        
        # Get total count first with the same filters, but no pagination
        count_query = f"SELECT COUNT(*) {base_query}{where_clause}"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()["count"]
        
        # Now get the actual data with pagination
        data_query = f"SELECT * {base_query}{where_clause} ORDER BY created_at DESC"
        
        # Only add LIMIT and OFFSET if they are provided and non-zero
        if limit > 0:
            data_query += " LIMIT %s"
            params.append(limit)
            
        if skip > 0:
            data_query += " OFFSET %s"
            params.append(skip)
        
        cursor.execute(data_query, params)
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries and normalize field names using Dutch-to-English mapping
        results = []
        for row in rows:
            result = dict(row)
            
            # Add field mapping for consistency with frontend
            # First, include the ID
            if 'id' in result:
                result['Id'] = str(result['id'])
            
            # Map the Dutch field names to English field names expected by frontend
            if 'url' in result:
                result['URL'] = result['url']
            if 'functie' in result:
                result['Functie'] = result['functie']
            if 'klant' in result:
                result['Klant'] = result['klant']
            if 'status' in result:
                result['Status'] = result['status']
            if 'functieomschrijving' in result:
                result['Functieomschrijving'] = result['functieomschrijving']
            if 'branche' in result:
                result['Branche'] = result['branche']
            if 'regio' in result:
                result['Regio'] = result['regio']
            if 'uren' in result:
                result['Uren'] = result['uren']
            if 'tarief' in result:
                result['Tarief'] = result['tarief']
            if 'geplaatst' in result:
                # Format the timestamp as a readable date
                if isinstance(result['geplaatst'], datetime.datetime):
                    result['Geplaatst'] = result['geplaatst'].strftime('%Y-%m-%d')
                else:
                    result['Geplaatst'] = str(result['geplaatst'])
            if 'sluiting' in result:
                # Format the timestamp as a readable date
                if isinstance(result['sluiting'], datetime.datetime):
                    result['Sluiting'] = result['sluiting'].strftime('%Y-%m-%d')
                else:
                    result['Sluiting'] = str(result['sluiting'])
            if 'top_match' in result:
                result['Top_Match'] = result['top_match']
            if 'match_toelichting' in result:
                result['Match_Toelichting'] = result['match_toelichting']
            if 'checked_resumes' in result:
                result['Checked_resumes'] = result['checked_resumes']
                
            results.append(result)
            
        # Return both the results and the total count
        return {
            "items": results,
            "total": total_count,
            "filtered_count": len(results)
        }
    except Exception as e:
        logger.error(f"Error getting vacancies: {str(e)}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_vacancy(vacancy_id: str) -> Optional[Dict[str, Any]]:
    """Get a vacancy by ID"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("SELECT * FROM vacancies WHERE id = %s", (vacancy_id,))
        row = cursor.fetchone()
        
        if row:
            result = dict(row)
            
            # Map fields for consistency with frontend (same as in get_all_vacancies)
            if 'id' in result:
                result['Id'] = str(result['id'])
            if 'url' in result:
                result['URL'] = result['url']
            if 'functie' in result:
                result['Functie'] = result['functie']
            if 'klant' in result:
                result['Klant'] = result['klant']
            if 'status' in result:
                result['Status'] = result['status']
            if 'functieomschrijving' in result:
                result['Functieomschrijving'] = result['functieomschrijving']
            if 'branche' in result:
                result['Branche'] = result['branche']
            if 'regio' in result:
                result['Regio'] = result['regio']
            if 'uren' in result:
                result['Uren'] = result['uren']
            if 'tarief' in result:
                result['Tarief'] = result['tarief']
            if 'geplaatst' in result:
                # Format the timestamp as a readable date
                if isinstance(result['geplaatst'], datetime.datetime):
                    result['Geplaatst'] = result['geplaatst'].strftime('%Y-%m-%d')
                else:
                    result['Geplaatst'] = str(result['geplaatst'])
            if 'sluiting' in result:
                # Format the timestamp as a readable date
                if isinstance(result['sluiting'], datetime.datetime):
                    result['Sluiting'] = result['sluiting'].strftime('%Y-%m-%d')
                else:
                    result['Sluiting'] = str(result['sluiting'])
            if 'top_match' in result:
                result['Top_Match'] = result['top_match']
            if 'match_toelichting' in result:
                result['Match_Toelichting'] = result['match_toelichting']
            if 'checked_resumes' in result:
                result['Checked_resumes'] = result['checked_resumes']
            
            return result
        return None
    except Exception as e:
        logger.error(f"Error getting vacancy {vacancy_id}: {str(e)}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def create_vacancy(vacancy_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new vacancy"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Map frontend/model field names to database field names
        field_mapping = {
            'URL': 'url',
            'Functie': 'functie',
            'Klant': 'klant',
            'Functieomschrijving': 'functieomschrijving',
            'Status': 'status',
            'Branche': 'branche',
            'Regio': 'regio',
            'Uren': 'uren',
            'Tarief': 'tarief',
            'Top_Match': 'top_match',
            'Match_Toelichting': 'match_toelichting',
            'Checked_resumes': 'checked_resumes'
        }
        
        # Convert field names to database column names
        db_data = {}
        for key, value in vacancy_data.items():
            # Skip the ID field (will be auto-generated)
            if key.lower() == 'id':
                continue
                
            # If the key is in the mapping, use the mapped name
            if key in field_mapping:
                db_data[field_mapping[key]] = value
            # If the key is already lowercase, assume it's a direct column name
            elif key.islower():
                db_data[key] = value
                
        # Prepare fields and values
        fields = list(db_data.keys())
        placeholders = ["%s"] * len(fields)
        values = [db_data[field] for field in fields]
        
        query = f"INSERT INTO vacancies ({', '.join(fields)}) VALUES ({', '.join(placeholders)}) RETURNING id"
        cursor.execute(query, values)
        
        vacancy_id = cursor.fetchone()[0]
        vacancy_data['id'] = vacancy_id
        vacancy_data['Id'] = str(vacancy_id)
        
        # Get the status for statistics updating
        status = db_data.get('status') or vacancy_data.get('Status') or 'Unknown'
        
        # Update vacancy statistics
        update_vacancy_statistics(conn, new_status=status)
        
        conn.commit()
        return vacancy_data
    except Exception as e:
        logger.error(f"Error creating vacancy: {str(e)}")
        if conn:
            conn.rollback()
        return vacancy_data
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def update_vacancy(vacancy_id: str, vacancy_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing vacancy"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # First, check if the status is being updated by getting the current status
        old_status = None
        if 'Status' in vacancy_data or 'status' in vacancy_data:
            cursor.execute("SELECT status FROM vacancies WHERE id = %s", (vacancy_id,))
            result = cursor.fetchone()
            if result:
                old_status = result[0]
        
        # Map frontend/model field names to database field names
        field_mapping = {
            'URL': 'url',
            'Functie': 'functie',
            'Klant': 'klant',
            'Functieomschrijving': 'functieomschrijving',
            'Status': 'status',
            'Branche': 'branche',
            'Regio': 'regio',
            'Uren': 'uren',
            'Tarief': 'tarief',
            'Top_Match': 'top_match',
            'Match_Toelichting': 'match_toelichting',
            'Checked_resumes': 'checked_resumes'
        }
        
        # Convert field names to database column names
        db_data = {}
        for key, value in vacancy_data.items():
            # Skip the ID field
            if key.lower() == 'id':
                continue
                
            # If the key is in the mapping, use the mapped name
            if key in field_mapping:
                db_data[field_mapping[key]] = value
            # If the key is already lowercase, assume it's a direct column name
            elif key.islower():
                db_data[key] = value
        
        # Prepare SET clause and values
        set_clause = []
        values = []
        
        for key, value in db_data.items():
            set_clause.append(f"{key} = %s")
            values.append(value)
        
        values.append(vacancy_id)
        
        query = f"UPDATE vacancies SET {', '.join(set_clause)} WHERE id = %s"
        cursor.execute(query, values)
        
        # Check if status is being updated, and update statistics if needed
        new_status = None
        if 'status' in db_data:
            new_status = db_data['status']
        elif 'Status' in vacancy_data:
            new_status = vacancy_data['Status']
            
        if old_status is not None and new_status is not None and old_status != new_status:
            # Status has changed, update statistics
            update_vacancy_statistics(conn, new_status=new_status, old_status=old_status)
        
        conn.commit()
        
        # Add ID back to the data for response
        vacancy_data['id'] = vacancy_id
        vacancy_data['Id'] = str(vacancy_id)
        
        return vacancy_data
    except Exception as e:
        logger.error(f"Error updating vacancy {vacancy_id}: {str(e)}")
        if conn:
            conn.rollback()
        return vacancy_data
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def delete_vacancy(vacancy_id: str) -> bool:
    """Delete a vacancy"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get the status of the vacancy before deleting it
        cursor.execute("SELECT status FROM vacancies WHERE id = %s", (vacancy_id,))
        result = cursor.fetchone()
        
        if not result:
            logger.warning(f"Vacancy with ID {vacancy_id} not found for deletion")
            return False
            
        old_status = result[0]
        
        # Delete the vacancy
        cursor.execute("DELETE FROM vacancies WHERE id = %s", (vacancy_id,))
        
        # Update the statistics
        update_vacancy_statistics(conn, old_status=old_status)
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error deleting vacancy {vacancy_id}: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def ensure_statistics_table(conn=None):
    """Ensure the vacancy_statistics table exists"""
    should_close_conn = False
    cursor = None
    try:
        if conn is None:
            conn = get_connection()
            should_close_conn = True
            
        cursor = conn.cursor()
        
        # Create the statistics table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vacancy_statistics (
            id SERIAL PRIMARY KEY,
            status VARCHAR(255) UNIQUE,
            count INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error creating statistics table: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if should_close_conn and conn:
            conn.close()

def update_vacancy_statistics(conn=None, new_status=None, old_status=None):
    """Update the vacancy statistics table when a vacancy is added, updated, or deleted"""
    should_close_conn = False
    cursor = None
    try:
        if conn is None:
            conn = get_connection()
            should_close_conn = True
            
        cursor = conn.cursor()
        
        # Ensure the statistics table exists
        ensure_statistics_table(conn)
        
        # If a vacancy was added or its status changed to new_status
        if new_status:
            # Try to update the count for the status
            cursor.execute("""
            INSERT INTO vacancy_statistics (status, count) 
            VALUES (%s, 1)
            ON CONFLICT (status) 
            DO UPDATE SET 
                count = vacancy_statistics.count + 1,
                last_updated = CURRENT_TIMESTAMP
            """, (new_status,))
        
        # If a vacancy was deleted or its status changed from old_status
        if old_status:
            # Decrement the count for the old status
            cursor.execute("""
            UPDATE vacancy_statistics 
            SET count = GREATEST(0, count - 1),
                last_updated = CURRENT_TIMESTAMP
            WHERE status = %s
            """, (old_status,))
        
        if should_close_conn:
            conn.commit()
        
        return True
    except Exception as e:
        logger.error(f"Error updating vacancy statistics: {str(e)}")
        if should_close_conn and conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if should_close_conn and conn:
            conn.close()

def rebuild_vacancy_statistics():
    """Rebuild the vacancy statistics from scratch by counting all vacancies"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Ensure the statistics table exists
        ensure_statistics_table(conn)
        
        # Clear existing statistics
        cursor.execute("TRUNCATE TABLE vacancy_statistics")
        
        # Get counts by status
        cursor.execute("""
        INSERT INTO vacancy_statistics (status, count)
        SELECT status, COUNT(*) 
        FROM vacancies 
        GROUP BY status
        """)
        
        conn.commit()
        logger.info("Vacancy statistics rebuilt successfully")
        return True
    except Exception as e:
        logger.error(f"Error rebuilding vacancy statistics: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_vacancy_statistics() -> Dict[str, int]:
    """Get the current vacancy statistics"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Ensure the statistics table exists
        ensure_statistics_table(conn)
        
        # Get the statistics
        cursor.execute("SELECT status, count FROM vacancy_statistics")
        rows = cursor.fetchall()
        
        # Convert to a dictionary
        stats = {row['status']: row['count'] for row in rows}
        
        # Get the total count
        cursor.execute("SELECT SUM(count) as total FROM vacancy_statistics")
        total = cursor.fetchone()
        if total and total['total']:
            stats['total'] = total['total']
        else:
            stats['total'] = 0
            
        return stats
    except Exception as e:
        logger.error(f"Error getting vacancy statistics: {str(e)}")
        return {'total': 0}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()