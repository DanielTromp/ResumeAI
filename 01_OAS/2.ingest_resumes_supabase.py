import os
import json
import time
import supabase
import tiktoken
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
import pandas as pd
from supabase import create_client

# Omgevingsvariabelen laden
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Verbinding maken met Supabase
try:
    client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)
    # Test connectie en leeg maken van de database
    client.table('01_OAS').delete().neq('id', 0).execute()
    print("✅ Supabase verbinding succesvol en database geleegd!")
except Exception as e:
    print(f"❌ Fout bij verbinden met Supabase: {str(e)}")
    exit(1)

# OpenAI client instellen
client_openai = OpenAI(api_key=OPENAI_API_KEY)

# Functie om embeddings te genereren
def get_embedding(text):
    response = client_openai.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding

# Functie om een lange tekst op te splitsen in chunks van max 500 tokens
def split_text(text, max_tokens=500):
    enc = tiktoken.get_encoding("cl100k_base")  # OpenAI tokenizer
    tokens = enc.encode(text)
    chunks = [tokens[i:i + max_tokens] for i in range(0, len(tokens), max_tokens)]
    return [enc.decode(chunk) for chunk in chunks]

# Functie om PDF-bestanden te lezen
def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()

# Map waar de PDF's staan
pdf_folder = "resumes/"
pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith(".pdf")]

if not pdf_files:
    print("❌ Geen PDF-bestanden gevonden in de map 'resumes/'.")
    exit(1)

# PDF's verwerken en in Supabase opslaan
for pdf_file in pdf_files:
    pdf_path = os.path.join(pdf_folder, pdf_file)
    naam = os.path.splitext(pdf_file)[0]  # Gebruik de bestandsnaam als naam van de kandidaat
    
    print(f"📄 Verwerken: {pdf_file}")

    # PDF omzetten naar tekst
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print(f"⚠️ Geen tekst gevonden in {pdf_file}, overslaan.")
        continue

    # Tekst opsplitsen in chunks
    chunks = split_text(text)

    # Chunks embedden en opslaan in Supabase
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        time.sleep(1)  # Voorkomen van API rate limiting

        # Opslaan in Supabase
        client.table("01_OAS").insert({
            "naam": naam,
            "cv_chunk": chunk,
            "embedding": embedding  # direct de lijst van floats
        }).execute()

    print(f"✅ CV '{naam}' succesvol opgeslagen met {len(chunks)} chunks.")

print("🚀 Alle CV's succesvol verwerkt en opgeslagen in Supabase!")
