# OpenAI Resume Matching System (Local Version)

A Python-based system that matches resumes with job vacancies using OpenAI's embeddings and GPT-4o-mini for evaluation. This version uses local CSV files and LanceDB for storage.

## About this project

This system processes resumes and job vacancies through several steps:
1. Ingesting resumes into LanceDB with vector embeddings
2. Processing new vacancies from Spinweb.nl
3. Matching resumes with vacancies using vector similarity
4. Evaluating matches using GPT-4o-mini
5. Updating vacancy statuses in CSV files

**Metadata:**
- **Author:** Daniel Tromp
- **Email:** drpgmtromp@gmail.com
- **Version:** 1.0.0
- **Created:** 2024-02-14
- **License:** MIT

## Scripts

### 1. Resume Ingestion
```bash
python 1.ingest_resumes_lancedb.py
```
Processes PDF resumes and stores them in LanceDB with vector embeddings.

### 2. Vacancy Processing
```bash
python 2.ingest_listings_spinweb_local.py
```
Fetches and processes new vacancies from Spinweb.nl into a local CSV file.

### 3. Resume Matching
```bash
python 3.match_resumes_local.py
```
Matches resumes with vacancies and evaluates candidates using GPT-4o-mini.

## Configuration

Update the `.env` file in the root directory with your credentials:

```env
# OpenAI API configuration
OPENAI_API_KEY=your_openai_api_key

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
cd 02_OCL
python 1.ingest_resumes_lancedb.py
python 2.ingest_listings_spinweb_local.py
python 3.match_resumes_local.py
```

## CSV Structure

The system uses a CSV file (`vacancies.csv`) with the following fields:
- URL (Text)
- Status (Text)
- Functie (Text)
- Klant (Text)
- Regio (Text)
- Uren (Text)
- Geplaatst (Date)
- Sluiting (Date)
- Functieomschrijving (Text)
- Top_Match (Number)
- Match_Toelichting (Text)
- Checked_resumes (Text)
- Tarief (Text)
- Branche (Text)

## Troubleshooting

- If OpenAI errors occur:
  - Check your API key
  - Verify you have sufficient credits
  - Check for rate limiting

- If LanceDB errors occur:
  - Verify the database directory exists
  - Check file permissions
  - Ensure proper table schema

- If CSV errors occur:
  - Check file permissions
  - Verify CSV structure
  - Ensure proper field types

## Support

For questions or issues, contact the author via the email provided above.