#!/usr/bin/env python3
"""
PostgreSQL Resume Manager

This script handles uploading, replacing, and deleting resume PDFs in PostgreSQL.
It performs the following tasks:
1. Upload new resumes (PDF files) to PostgreSQL
2. Replace existing resumes
3. Delete resumes from PostgreSQL
4. List all resumes in PostgreSQL

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
import shutil
from pathlib import Path
from typing import List, Optional

# Third-party imports
import psycopg2
import psycopg2.extras
import tiktoken
from dotenv import load_dotenv
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

def upload_resume(conn, pdf_path):
    """Upload a new resume to PostgreSQL"""
    pdf_file = os.path.basename(pdf_path)
    name = os.path.splitext(pdf_file)[0]  # Use the file name as the candidate's name
    
    print(f"📄 Processing: {pdf_file}")
    
    # Move file to resumes folder if it's not already there
    target_path = os.path.join(PDF_FOLDER, pdf_file)
    if pdf_path != target_path:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        shutil.copy2(pdf_path, target_path)
        print(f"📁 Copied resume to: {target_path}")
    
    # Convert PDF to text
    text = extract_text_from_pdf(target_path)
    if not text:
        print(f"⚠️ No text found in {pdf_file}, skipping.")
        return False
    
    # Split text into chunks
    chunks = split_text(text)
    
    try:
        cursor = conn.cursor()
        
        # Check if resume already exists
        cursor.execute(
            f"SELECT COUNT(*) FROM {PG_TABLE} WHERE filename = %s",
            (pdf_file,)
        )
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"⚠️ Resume '{name}' already exists. Use replace option to update.")
            cursor.close()
            return False
        
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
        print(f"❌ Error uploading resume: {str(e)}")
        return False

def replace_resume(conn, pdf_path):
    """Replace an existing resume in PostgreSQL"""
    pdf_file = os.path.basename(pdf_path)
    name = os.path.splitext(pdf_file)[0]
    
    print(f"🔄 Replacing: {pdf_file}")
    
    try:
        cursor = conn.cursor()
        
        # Check if resume exists
        cursor.execute(
            f"SELECT COUNT(*) FROM {PG_TABLE} WHERE filename = %s",
            (pdf_file,)
        )
        count = cursor.fetchone()[0]
        
        if count == 0:
            print(f"⚠️ Resume '{name}' does not exist. Use upload option to add.")
            cursor.close()
            return False
        
        # Delete existing resume
        cursor.execute(
            f"DELETE FROM {PG_TABLE} WHERE filename = %s",
            (pdf_file,)
        )
        conn.commit()
        
        cursor.close()
        
        # Upload the new version
        return upload_resume(conn, pdf_path)
    
    except Exception as e:
        conn.rollback()
        print(f"❌ Error replacing resume: {str(e)}")
        return False

def delete_resume(conn, pdf_file):
    """Delete a resume from PostgreSQL"""
    name = os.path.splitext(pdf_file)[0]
    
    print(f"🗑️ Deleting: {pdf_file}")
    
    # Check if file exists in resumes folder
    pdf_path = os.path.join(PDF_FOLDER, pdf_file)
    
    try:
        cursor = conn.cursor()
        
        # Delete from PostgreSQL
        cursor.execute(
            f"DELETE FROM {PG_TABLE} WHERE filename = %s",
            (pdf_file,)
        )
        conn.commit()
        
        # If file exists, delete it
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            print(f"🗑️ Deleted file: {pdf_path}")
        
        cursor.close()
        print(f"✅ Resume '{name}' successfully deleted.")
        return True
    
    except Exception as e:
        conn.rollback()
        print(f"❌ Error deleting resume: {str(e)}")
        return False

def list_resumes(conn):
    """List all resumes in PostgreSQL"""
    try:
        cursor = conn.cursor()
        
        # Get distinct filenames
        cursor.execute(
            f"SELECT DISTINCT name, filename FROM {PG_TABLE} ORDER BY name"
        )
        resumes = cursor.fetchall()
        
        print(f"\n📋 Found {len(resumes)} resumes in the database:")
        for i, (name, filename) in enumerate(resumes):
            print(f"{i+1}. {name} ({filename})")
        
        cursor.close()
        return resumes
    
    except Exception as e:
        print(f"❌ Error listing resumes: {str(e)}")
        return []

def process_directory(conn, directory, action="upload"):
    """Process all PDF files in a directory"""
    pdf_files = [f for f in os.listdir(directory) if f.endswith(".pdf")]
    
    if not pdf_files:
        print(f"❌ No PDF files found in {directory}.")
        return False
    
    success_count = 0
    for pdf_file in pdf_files:
        pdf_path = os.path.join(directory, pdf_file)
        
        if action == "upload":
            if upload_resume(conn, pdf_path):
                success_count += 1
        elif action == "replace":
            if replace_resume(conn, pdf_path):
                success_count += 1
    
    print(f"✅ Processed {success_count} of {len(pdf_files)} resumes.")
    return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Manage resumes in PostgreSQL")
    
    # Create a mutually exclusive group for actions
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument("--upload", help="Upload a resume (PDF file)", metavar="FILE")
    action_group.add_argument("--upload-dir", help="Upload all resumes in directory", metavar="DIR")
    action_group.add_argument("--replace", help="Replace an existing resume", metavar="FILE")
    action_group.add_argument("--replace-dir", help="Replace all resumes in directory", metavar="DIR")
    action_group.add_argument("--delete", help="Delete a resume", metavar="FILE")
    action_group.add_argument("--list", action="store_true", help="List all resumes")
    
    args = parser.parse_args()
    
    # Connect to PostgreSQL
    conn = connect_to_postgres()
    
    try:
        if args.upload:
            upload_resume(conn, args.upload)
        elif args.upload_dir:
            process_directory(conn, args.upload_dir, "upload")
        elif args.replace:
            replace_resume(conn, args.replace)
        elif args.replace_dir:
            process_directory(conn, args.replace_dir, "replace")
        elif args.delete:
            delete_resume(conn, args.delete)
        elif args.list:
            list_resumes(conn)
    finally:
        # Close connection
        conn.close()
        print("✅ PostgreSQL connection closed")

if __name__ == "__main__":
    main()