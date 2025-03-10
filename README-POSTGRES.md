# PostgreSQL with pgvector for ResumeAI

This document describes how to set up and use PostgreSQL with pgvector extension for the ResumeAI project.

## Quick Reference

```bash
# Start PostgreSQL with Docker
./manage.sh docker-up

# Initialize database
./manage.sh init-db

# Backup everything (including database)
./manage.sh backup

# Restore from backup
./manage.sh restore backups/resumeai_backup_20250310_123456.tar.gz
```

For complete backup and restore instructions, see [README-BACKUP.md](README-BACKUP.md).

## Setup Instructions

### Step 1: Start the Docker containers

```bash
# Start all containers (PostgreSQL, backend, frontend)
./manage.sh docker-up
```

### Step 2: Initialize the database

If running for the first time, initialize the database:

```bash
# Run the initialization script
./manage.sh init-db
```

This script will:
1. Create the PostgreSQL database if it doesn't exist
2. Set up the pgvector extension
3. Create the necessary tables and functions

## Resume Management

The `postgres_resume_manager.py` script provides functionality to manage resumes in the PostgreSQL database.

### Listing resumes

```bash
# List all resumes in the database
python -m backend.app.postgres_resume_manager --list
```

### Uploading resumes

```bash
# Upload a single resume
python -m backend.app.postgres_resume_manager --upload /path/to/resume.pdf

# Upload all resumes in a directory
python -m backend.app.postgres_resume_manager --upload-dir /path/to/resumes/
```

### Replacing resumes

```bash
# Replace a single resume
python -m backend.app.postgres_resume_manager --replace /path/to/resume.pdf

# Replace all resumes in a directory
python -m backend.app.postgres_resume_manager --replace-dir /path/to/resumes/
```

### Deleting resumes

```bash
# Delete a resume (specify just the filename, not the path)
python -m backend.app.postgres_resume_manager --delete "John Doe.pdf"
```

## Importing Resumes to PostgreSQL

You can import resume PDFs directly to PostgreSQL using the `import_resumes_to_postgres.py` script.

```bash
# Import resumes from the default directory
python -m backend.app.import_resumes_to_postgres

# Clear database before import
python -m backend.app.import_resumes_to_postgres --clear

# Import from a specific directory
python -m backend.app.import_resumes_to_postgres --dir /path/to/resumes/
```

The script will:
1. Connect to PostgreSQL
2. Process all PDF files in the specified directory
3. Generate embeddings for each resume
4. Insert the data into the PostgreSQL database
5. Verify the import was successful

## Environment Variables

The following environment variables can be set in a `.env` file:

### PostgreSQL
- `PG_HOST`: PostgreSQL host (default: "localhost")
- `PG_PORT`: PostgreSQL port (default: "5432")
- `PG_USER`: PostgreSQL username (default: "postgres")
- `PG_PASSWORD`: PostgreSQL password (default: "postgres")
- `PG_DATABASE`: PostgreSQL database name (default: "resumeai")

### OpenAI
- `OPENAI_API_KEY`: Your OpenAI API key
- `EMBEDDING_MODEL`: The embedding model to use (default: "text-embedding-ada-002")

### Resume Storage
- `PDF_FOLDER`: Directory to store PDF files (default: "app/resumes/")

## Database Schema

The PostgreSQL database has the following schema:

### `resumes` Table

| Column | Type | Description |
|--------|------|-------------|
| id | serial | Primary key |
| name | text | Name of the candidate |
| filename | text | Filename of the resume PDF |
| cv_chunk | text | Chunk of text from the resume |
| embedding | vector(1536) | Vector embedding of the text chunk |
| created_at | timestamptz | Creation timestamp |
| updated_at | timestamptz | Last update timestamp |

### `match_resumes` Function

A function that finds the best matching resumes for a given query embedding:

```sql
match_resumes(
    query_embedding vector,
    match_threshold double precision,
    match_count integer
)
```

Returns a table with the following columns:
- `name`: Name of the candidate
- `cv_chunk`: Matching text chunk from the resume
- `similarity`: Similarity score (0-1, higher is better)

## Example Usage in Python

```python
import psycopg2
import psycopg2.extras
from openai import OpenAI

# Connect to PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    port="5432",
    user="postgres",
    password="postgres",
    database="resumeai"
)

# Set up OpenAI client
client = OpenAI(api_key="your-openai-api-key")

# Generate embedding for a job description
def get_embedding(text):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding

# Match resumes against a job description
def match_resumes(job_description, match_threshold=0.75, match_count=5):
    # Generate embedding for job description
    job_embedding = get_embedding(job_description)
    
    # Find matching resumes
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(
        "SELECT * FROM match_resumes(%s, %s, %s)",
        (job_embedding, match_threshold, match_count)
    )
    
    matches = cursor.fetchall()
    cursor.close()
    
    return matches

# Example usage
job_description = "Looking for a Python developer with experience in machine learning..."
matches = match_resumes(job_description)

for match in matches:
    print(f"Candidate: {match['name']}")
    print(f"Similarity: {match['similarity']:.2f}")
    print(f"Matching text: {match['cv_chunk'][:100]}...")
    print("-----")
```