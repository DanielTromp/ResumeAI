import os
import time
import lancedb
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
import tiktoken

# Omgevingsvariabelen laden
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# LanceDB database initialiseren
db = lancedb.connect("./lancedb")

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

# Maak de tabel aan als deze nog niet bestaat
table = db.create_table(
    "cv_chunks",
    data=[{
        "naam": "dummy",
        "cv_chunk": "dummy",
        "embedding": [0.0] * 1536  # Expliciet een vector van floats met de juiste dimensie
    }],
    mode="overwrite"
)

# Configureer vector search index
table.create_index(
    "embedding",
    index="IVF_PQ",
    metric="cosine",
    replace=True
)

# Map waar de PDF's staan
pdf_folder = "resumes/"
pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith(".pdf")]

if not pdf_files:
    print("❌ Geen PDF-bestanden gevonden in de map 'resumes/'.")
    exit(1)

# PDF's verwerken en in LanceDB opslaan
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

    # Chunks embedden en opslaan in LanceDB
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        time.sleep(1)  # Voorkomen van API rate limiting

        # Opslaan in LanceDB
        table.add([{
            "naam": naam,
            "cv_chunk": chunk,
            "embedding": embedding
        }])

    print(f"✅ CV '{naam}' succesvol opgeslagen met {len(chunks)} chunks.")

print("🚀 Alle CV's succesvol verwerkt en opgeslagen in LanceDB!")