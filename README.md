# Spinweb Vacancy Scraper & Resume Matcher

A Python system that automatically scrapes Spinweb vacancies, stores them in NocoDB, and matches them with CVs.

## About this project

This system processes vacancies and CVs in an integrated process:
1. Logging into Spinweb and retrieving new vacancy listings
2. Comparing with existing vacancies in NocoDB
3. Extraction of vacancy details
4. Matching CVs with new vacancies via vector similarity
5. Evaluating matches using GPT-4o-mini
6. Updating vacancy statuses in NocoDB

**Metadata:**
- **Author:** Daniel Tromp
- **Email:** drpgmtromp@gmail.com
- **Version:** 1.5.0
- **Created:** 2025-02-11
- **Updated:** 2025-05-25
- **License:** MIT
- **Repository:** https://github.com/DanielTromp/ResumeAI

## Setup

1. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/MacOS
python3 -m venv venv
source venv/bin/activate
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:
```bash
playwright install
```

4. Copy the `.env.example` file to `.env`:
```bash
cp .env.example .env
```

5. Update the `.env` file with your own credentials:
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
SOURCE_URL=your_desired_url

# Excluded clients (optional)
EXCLUDED_CLIENTS=Client1,Client2,Client3
```

## NocoDB Setup

1. Create a new NocoDB database
2. Create a table with the following fields:
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

3. Generate an API token in NocoDB and fill it in the `.env` file

## Usage

Run the combined script:
```bash
cd 03_ONS
python combined_process.py
```

This script automatically performs the following:
- Scraping new vacancies from Spinweb
- Cleaning up closed listings
- Matching vacancies with CVs via vector similarity
- Evaluating matches with GPT-4o-mini
- Updating the results in NocoDB

## Maintenance

To deactivate the virtual environment:
```bash
deactivate
```

To update the dependencies:
```bash
pip install -r requirements.txt --upgrade
```

## Updates

To fetch the latest version:
```bash
# Save local changes
git stash

# Pull updates
git pull

# Apply local changes if needed
git stash pop

# Update dependencies if needed
pip install -r requirements.txt
```

## Troubleshooting

- For Playwright errors, try reinstalling the browsers:
```bash
playwright install
```

- For NocoDB errors, check if:
  - Your API token is correct
  - The URL, project, and table names are correct
  - The field names are correct (case-sensitive)

- For OpenAI errors, check if:
  - Your API key is correct
  - You have sufficient credits

- For URL normalization problems:
  - Check the `normalize_url` and `normalize_url_for_crawler` methods in `nocodb_client.py`
  - Ensure URLs are consistently normalized throughout the code

## Support

For questions or issues, contact the author via the contact details above.