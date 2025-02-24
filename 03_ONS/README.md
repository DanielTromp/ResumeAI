# OpenAI Resume Matching System (NocoDB Version)

A Python system that matches CVs with job vacancies using OpenAI's embeddings and GPT-4o-mini for evaluation. This version uses NocoDB and Supabase for storage.

## About this project

This system processes CVs and job vacancies in an integrated process:
1. Ingesting CVs into Supabase with vector embeddings
2. Processing new vacancies from Spinweb.nl
3. Matching CVs with vacancies using vector similarity
4. Evaluating matches using GPT-4o-mini
5. Updating vacancy statuses in NocoDB

**Metadata:**
- **Author:** Daniel Tromp
- **Email:** drpgmtromp@gmail.com
- **Version:** 2.0.0
- **Created:** 2024-02-14
- **Updated:** 2025-05-25
- **License:** MIT

## Scripts

### 1. Combined Vacancy & CV Matching Process
```bash
python combined_process.py
```
Performs the complete process in a single step:
- Scraping new vacancies from Spinweb
- Storing vacancies in NocoDB
- Matching CVs with vacancies
- Evaluating candidates using GPT-4o-mini
- Updating results in NocoDB

## Configuration

Update the `.env` file in the root directory with your credentials:

```env
# OpenAI API configuration
OPENAI_API_KEY=your_openai_api_key

# NocoDB configuration
NOCODB_URL=your_nocodb_url
NOCODB_TOKEN=your_nocodb_token
NOCODB_PROJECT=your_project_name
NOCODB_TABLE=your_table_name

# Supabase configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Spinweb configuration
SPINWEB_USER=your_username
SPINWEB_PASS=your_password

# Excluded clients (optional)
EXCLUDED_CLIENTS=Client1,Client2,Client3
```

## Usage

From the root directory:

1. Place PDF CVs in the `resumes/` folder

2. Activate the virtual environment (from the root directory):
```bash
# Windows
.venv\Scripts\activate

# Unix or MacOS
source .venv/bin/activate
```

3. Run the combined script:
```bash
cd 03_ONS
python combined_process.py
```

## NocoDB Setup

1. Create a new table in your NocoDB database with the following fields:
   - `URL` (Text)
   - `Status` (Single Select)
   - `Functie` (Text)
   - `Klant` (Text)
   - `Branche` (Text)
   - `Regio` (Text)
   - `Uren` (Text)
   - `Tarief` (Text)
   - `Geplaatst` (Date)
   - `Sluiting` (Date)
   - `Functieomschrijving` (Long Text)
   - `Top_Match` (Number)
   - `Match Toelichting` (Long Text)
   - `Checked_resumes` (Text)

2. Generate an API token in NocoDB and fill it in the `.env` file

## Components

### NocoDBClient

The `NocoDBClient` class (in `components/nocodb_client.py`) handles communication with the NocoDB database:

- `update_record`: Updates an existing record or adds a new record
- `normalize_url`: Normalizes URLs for consistent database storage
- `normalize_url_for_crawler`: Normalizes URLs for use in the crawler (with protocol)
- `get_existing_listings`: Retrieves all existing listings from the database
- `cleanup_closed_listings`: Removes all listings with status 'Closed'

### Combined process

The `combined_process.py` script integrates:
- Logging into Spinweb with Playwright
- Retrieving and processing vacancies
- CV matching through vector similarity in Supabase
- Evaluating candidates with GPT-4o-mini
- Updating all results in NocoDB

## Troubleshooting

- For OpenAI errors:
  - Check your API key
  - Verify that you have sufficient credits
  - Check for rate limiting

- For NocoDB errors:
  - Verify your API token
  - Check the table and field names
  - Ensure the field types are correct

- For Supabase errors:
  - Check your connection credentials
  - Verify that the vector table exists
  - Ensure the RPC function is properly set up

- For URL normalization problems:
  - Check the `normalize_url` and `normalize_url_for_crawler` methods
  - Ensure URLs are consistently normalized throughout the code

## Support

For questions or issues, contact the author via the email address above.
