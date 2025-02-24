#!/usr/bin/env python3
"""
Ingest local resumes into Supabase vector table

This script ingests local resumes into Supabase vector table.
It performs the following tasks:
1. Connect to Supabase
2. Test connection and clear the database
3. Set up OpenAI client
4. Function to generate embeddings
5. Function to split a long text into chunks of max 500 tokens
6. Function to read local PDF files
7. List all the local PDF files in the PDF_FOLDER directory
8. Process all the local PDF files in the PDF_FOLDER directory

Author: Daniel Tromp
Email: drpgmtromp@gmail.com
Version: 0.0.1
Created: 2025-02-11
Updated: 2025-02-17
License: MIT
Repository: https://github.com/DanielTromp/ResumeAI
"""

# Standard library imports
import os
import time
import tiktoken
from openai import OpenAI
from pypdf import PdfReader
from supabase import create_client

# Project specific imports
from config import *

# Connect to Supabase and clear the database every time
try:
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    # Test connection and clear the database
    client.table(RESUME_VECTOR_TABLE).delete().neq('id', 0).execute()
    print("✅ Supabase connection successful and database cleared!")
except Exception as e:
    print(f"❌ Error connecting to Supabase: {str(e)}")
    exit(1)

# Set up OpenAI client
client_openai = OpenAI(api_key=OPENAI_API_KEY)

# Function to generate embeddings
def get_embedding(text):
    response = client_openai.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL
    )
    return response.data[0].embedding

# Function to split a long text into chunks of max 500 tokens
def split_text(text, max_tokens=500):
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    chunks = [tokens[i:i + max_tokens] for i in range(0, len(tokens), max_tokens)]
    return [enc.decode(chunk) for chunk in chunks]

# Function to read local PDF files
def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()

# List all the local PDF files in the PDF_FOLDER directory
pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.endswith(".pdf")]

if not pdf_files:
    print("❌ No PDF files found in the " + PDF_FOLDER + " directory.")
    exit(1)

# Process all the local PDF files in the PDF_FOLDER directory
for pdf_file in pdf_files:
    pdf_path = os.path.join(PDF_FOLDER, pdf_file)
    name = os.path.splitext(pdf_file)[0]  # Use the file name as the candidate's name

    print(f"📄 Processing: {pdf_file}")

    # Convert PDF to text
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print(f"⚠️ No text found in {pdf_file}, skipping.")
        continue

    # Split text into chunks
    chunks = split_text(text)

    # Embed chunks and save to Supabase
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        time.sleep(1)  # Prevent API rate limiting

        # Save to Supabase
        client.table(RESUME_VECTOR_TABLE).insert({
            "name": name,
            "cv_chunk": chunk,
            "embedding": embedding
        }).execute()

    print(f"✅ CV '{name}' successfully saved with {len(chunks)} chunks.")

print("🚀 All CVs successfully processed and saved in Supabase!")
