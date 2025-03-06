#!/usr/bin/env python3
"""
Import resumes from PDF files to PostgreSQL with pgvector

This script imports resume PDFs into a PostgreSQL database with pgvector.
It processes the resumes in the specified directory and saves their vector embeddings.

Author: Daniel Tromp
Email: drpgmtromp@gmail.com
Version: 0.1.0
Created: 2025-03-05
License: MIT
Repository: https://github.com/DanielTromp/ResumeAI
"""

# Standard library imports
import os
import time
import argparse
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
import tiktoken
from pypdf import PdfReader
from openai import OpenAI

# Load environment variables
load_dotenv()

# Configuration
PDF_FOLDER = os.getenv("PDF_FOLDER", "app/resumes/")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")

# PostgreSQL configuration
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")
PG_DATABASE = os.getenv("PG_DATABASE", "resumeai")
PG_TABLE = "resumes"

# Set up OpenAI client
client_openai = OpenAI(api_key=OPENAI_API_KEY)

def connect_to_postgres():
    """Connect to PostgreSQL and return connection"""
    print(f"Connecting to PostgreSQL at {PG_HOST}:{PG_PORT}")
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            database=PG_DATABASE
        )
        print("✅ Connected to PostgreSQL")
        return conn
    except Exception as e:
        print(f"❌ Error connecting to PostgreSQL: {str(e)}")
        raise e

def get_embedding(text):
    """Generate embedding for text using OpenAI API"""
    response = client_openai.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL
    )
    return response.data[0].embedding

def split_text(text, max_tokens=500):
    """Split a long text into chunks of max tokens"""
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    chunks = [tokens[i:i + max_tokens] for i in range(0, len(tokens), max_tokens)]
    return [enc.decode(chunk) for chunk in chunks]

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()

def clear_database(conn):
    """Clear existing data in the database"""
    try:
        cursor = conn.cursor()
        cursor.execute(f"TRUNCATE TABLE {PG_TABLE} RESTART IDENTITY")
        conn.commit()
        cursor.close()
        print("✅ Database cleared")
    except Exception as e:
        conn.rollback()
        print(f"❌ Error clearing database: {str(e)}")
        raise e

def process_resume(conn, pdf_path):
    """Process a single resume and insert into database"""
    pdf_file = os.path.basename(pdf_path)
    name = os.path.splitext(pdf_file)[0]
    
    print(f"📄 Processing: {pdf_file}")
    
    # Convert PDF to text
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print(f"⚠️ No text found in {pdf_file}, skipping.")
        return False
    
    # Split text into chunks
    chunks = split_text(text)
    
    try:
        cursor = conn.cursor()
        
        # Embed chunks and save to PostgreSQL
        for i, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)
            time.sleep(1)  # Prevent API rate limiting
            
            # Save to PostgreSQL
            cursor.execute(
                f"""
                INSERT INTO {PG_TABLE} (name, filename, cv_chunk, embedding)
                VALUES (%s, %s, %s, %s)
                """,
                (name, pdf_file, chunk, embedding)
            )
        
        conn.commit()
        cursor.close()
        print(f"✅ CV '{name}' successfully saved with {len(chunks)} chunks.")
        return True
    
    except Exception as e:
        conn.rollback()
        print(f"❌ Error processing resume: {str(e)}")
        return False

def process_directory(conn, directory):
    """Process all PDF files in a directory"""
    pdf_files = [f for f in os.listdir(directory) if f.endswith(".pdf")]
    
    if not pdf_files:
        print(f"❌ No PDF files found in {directory}.")
        return False
    
    print(f"Found {len(pdf_files)} PDF files in {directory}")
    
    success_count = 0
    for pdf_file in pdf_files:
        pdf_path = os.path.join(directory, pdf_file)
        if process_resume(conn, pdf_path):
            success_count += 1
    
    print(f"✅ Processed {success_count} of {len(pdf_files)} resumes.")
    return True

def verify_import(conn):
    """Verify the import by counting records"""
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {PG_TABLE}")
        count = cursor.fetchone()[0]
        cursor.close()
        print(f"✅ Verification complete: {count} records in PostgreSQL")
        return count
    except Exception as e:
        print(f"❌ Error verifying import: {str(e)}")
        raise e

def main():
    """Main function to import resumes to PostgreSQL"""
    parser = argparse.ArgumentParser(description="Import resumes to PostgreSQL")
    parser.add_argument("--dir", help="Directory containing resume PDFs", default=PDF_FOLDER)
    parser.add_argument("--clear", action="store_true", help="Clear database before import")
    
    args = parser.parse_args()
    
    print("🔄 Starting resume import to PostgreSQL")
    
    # Connect to PostgreSQL
    conn = connect_to_postgres()
    
    try:
        # Clear database if requested
        if args.clear:
            clear_database(conn)
        
        # Process resumes
        process_directory(conn, args.dir)
        
        # Verify import
        record_count = verify_import(conn)
        
        print(f"🎉 Import completed successfully! {record_count} records imported.")
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
    finally:
        # Close PostgreSQL connection
        if conn:
            conn.close()
            print("✅ PostgreSQL connection closed")

if __name__ == "__main__":
    main()