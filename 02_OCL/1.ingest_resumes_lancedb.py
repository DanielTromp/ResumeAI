#!/usr/bin/env python3
"""
Ingestie van lokale resumes in LanceDB

Dit script leest de PDF's uit de map PDF_FOLDER, gebruikt Docling
voor het extraheren en splitsen van de tekst en berekent embeddings
via OpenAI. Vervolgens worden de chunks met hun embeddings in een
lokale LanceDB-collectie opgeslagen.

Author: Daniel Tromp
Email: drpgmtromp@gmail.com
Version: 1.0.0
License: MIT
"""

import os
import time
from openai import OpenAI
import tiktoken
import lancedb
import pyarrow as pa
from PyPDF2 import PdfReader
import re
import logging

# Projectspecifieke configuratie importeren
from config import *

# Stel OpenAI client in
client_openai = OpenAI(api_key=OPENAI_API_KEY)

# Initialiseer token encoder
enc = tiktoken.encoding_for_model("gpt-4o-mini")

def get_embedding(text: str) -> list[float]:
    """Genereert een embedding voor de gegeven tekst via OpenAI."""
    response = client_openai.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL
    )
    return response.data[0].embedding

def ensure_lancedb_collection():
    """
    Verbindt met LanceDB en creëert de 'resumes'-collectie als deze niet bestaat.
    Maakt de database leeg bij de start.
    """
    db = lancedb.connect('lancedb')
    try:
        # Probeer eerst de bestaande tabel te verwijderen
        try:
            db.drop_table("resumes")
            logging.info("Bestaande 'resumes' tabel verwijderd")
        except:
            logging.info("Geen bestaande 'resumes' tabel gevonden om te verwijderen")

        # Schema definiëren met PyArrow
        schema = pa.schema([
            pa.field("name", pa.string()),
            pa.field("cv_chunk", pa.string()),
            pa.field("embedding", pa.list_(pa.float32(), 1536))
        ])
        
        # Nieuwe lege tabel aanmaken met het PyArrow schema
        table = db.create_table("resumes", schema=schema)
        logging.info("Nieuwe lege 'resumes' tabel aangemaakt")
        return table
        
    except Exception as e:
        logging.error(f"Fout bij het (her)initialiseren van de database: {e}")
        raise

def extract_text(pdf_path: str) -> str:
    """Extraheert tekst uit een PDF bestand."""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def split_text(text: str, max_tokens: int = 500) -> list[str]:
    """Splitst tekst in chunks van ongeveer max_tokens tokens."""
    # Verwijder overtollige whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Split op zinnen (ruw)
    sentences = re.split(r'[.!?]+', text)
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Schat aantal tokens (ruw)
        sentence_tokens = len(sentence.split())
        
        if current_length + sentence_tokens > max_tokens and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_length = 0
            
        current_chunk.append(sentence)
        current_length += sentence_tokens
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def ingest_resume(pdf_path: str, candidate_name: str, collection) -> None:
    """Verwerkt een PDF: extraheert de tekst, splitst in chunks, berekent embeddings en slaat ze op in LanceDB."""
    # Gebruik onze eigen functies in plaats van docling
    text = extract_text(pdf_path)
    chunks = split_text(text, max_tokens=500)
    
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        time.sleep(1)  # Voorkom API rate limiting
        
        # Data toevoegen met de juiste kolomnamen
        collection.add([{
            "name": candidate_name,
            "cv_chunk": chunk,
            "embedding": embedding
        }])
    
    print(f"✅ CV '{candidate_name}' succesvol ingeladen met {len(chunks)} chunks.")

def main():
    # Verbind met LanceDB en verkrijg de 'resumes'-collectie
    collection = ensure_lancedb_collection()
    
    # Zoek naar alle PDF's in de map PDF_FOLDER
    pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.endswith(".pdf")]
    if not pdf_files:
        print(f"❌ Geen PDF bestanden gevonden in de map {PDF_FOLDER}")
        return
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(PDF_FOLDER, pdf_file)
        # Gebruik de bestandsnaam (zonder extensie) als kandidaatnaam
        candidate_name = os.path.splitext(pdf_file)[0]
        print(f"📄 Verwerken: {pdf_file}")
        try:
            ingest_resume(pdf_path, candidate_name, collection)
        except Exception as e:
            print(f"⚠️ Fout bij verwerken van {pdf_file}: {e}")
    
    print("🚀 Alle CV's succesvol ingeladen in LanceDB!")

if __name__ == "__main__":
    main() 