# OpenAI Resume Matching System (Airtable Version)

A Python-based system that matches resumes with job vacancies using OpenAI's embeddings and GPT-4o-mini for evaluation. This version uses Airtable and Supabase for storage.

## About this project

This system processes resumes and job vacancies through several steps:
1. Ingesting resumes into Supabase with vector embeddings
2. Processing new vacancies from Spinweb.nl
3. Matching resumes with vacancies using vector similarity
4. Evaluating matches using GPT-4o-mini
5. Updating vacancy statuses in Airtable

**Metadata:**
- **Author:** Daniel Tromp
- **Email:** drpgmtromp@gmail.com
- **Version:** 1.0.0
- **Created:** 2024-02-14
- **License:** MIT

## Scripts

### 1. Resume Ingestion
```bash
python 1.ingest_resumes_supabase.py
```
Processes PDF resumes and stores them in Supabase with vector embeddings.

### 2. Vacancy Processing
```bash
python 2.ingest_listings_spinweb_airtable.py
```
Fetches and processes new vacancies from Spinweb.nl into Airtable.

### 3. Resume Matching
```bash
python 3.match_resumes_airtable.py
```
Matches resumes with vacancies and evaluates candidates using GPT-4o-mini.

## Configuration

Update the `.env` file in the root directory with your credentials:

```env
# OpenAI API configuration
OPENAI_API_KEY=your_openai_api_key

# Airtable configuration
AIRTABLE_API_KEY=your_airtable_api_key
AIRTABLE_BASE_ID=your_base_id

# Supabase configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Spinweb configuration
SPINWEB_USER=your_username
SPINWEB_PASS=your_password
```

## Usage

From the root directory:

1. Place PDF resumes in the `resumes/` folder

2. Activate the virtual environment (from root directory):
```bash
# On Windows
.venv\Scripts\activate

# On Unix or MacOS
source .venv/bin/activate
```

3. Run the scripts in order:
```bash
cd 01_OAS
python 1.ingest_resumes_supabase.py
python 2.ingest_listings_spinweb_airtable.py
python 3.match_resumes_airtable.py
```

## Airtable Setup

1. Create two tables in your Airtable base:
   - Main table (AIRTABLE_TABLE1): For vacancies
   - Exclusion table (AIRTABLE_TABLE2): For excluded clients

2. Required fields in the main table:
   - Status (Single Select)
   - URL (Text)
   - Functie (Text)
   - Klant (Text)
   - Regio (Text)
   - Uren (Text)
   - Geplaatst (Date)
   - Sluiting (Date)
   - Functieomschrijving (Long Text)
   - Top_Match (Number)
   - Match_Toelichting (Long Text)
   - Checked_resumes (Text)
   - Tarief (Text)
   - Branche (Text)

## Troubleshooting

- If OpenAI errors occur:
  - Check your API key
  - Verify you have sufficient credits
  - Check for rate limiting

- If Airtable errors occur:
  - Verify your API key and Base ID
  - Check table and field names
  - Ensure proper field types

- If Supabase errors occur:
  - Check your connection credentials
  - Verify the vector table exists
  - Ensure the RPC function is properly set up

## Support

For questions or issues, contact the author via the email provided above.
