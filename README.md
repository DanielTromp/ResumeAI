# Spinweb Vacancy Scraper

A Python script that automatically scrapes Spinweb vacancies and uploads them to Airtable.

## About this project

This script crawls the Spinweb website to find new vacancies and uploads them to Airtable.
It performs the following tasks:
1. Logging in to Spinweb
2. Fetching new vacancy listings
3. Comparing with existing listings in Airtable
4. Extraction of vacancy details
5. Uploading new vacancies to Airtable

**Metadata:**
- **Author:** Daniel Tromp
- **Email:** drpgmtromp@gmail.com
- **Version:** 1.0.0
- **Created:** 2025-02-11
- **Updated:** 2025-02-11
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

# Airtable configuration
AIRTABLE_API_KEY=your_airtable_api_key
AIRTABLE_BASE_ID=your_base_id
AIRTABLE_TABLE_NAME_PROCESSED=Aanvragen
AIRTABLE_TABLE_NAME_LISTINGS=Listings

# Spinweb configuration
SPINWEB_USER=your_username
SPINWEB_PASS=your_password
SOURCE_URL=your_desired_url
```

## Airtable Setup

1. Create a new Airtable base
2. Create two tables:
   - `Aanvragen`: For new vacancies
     - Fields: URL (Text), Status (Single Select), Functie (Text), Klant (Text), Branche (Text), Regio (Text), Uren (Text), Tarief (Text), Geplaatst (Date), Sluiting (Date), Functieomschrijving (Long Text)
   - `Listings`: For processed listings
     - Fields: Listing (Text)
3. Copy the Base ID from the Airtable API documentation
4. Generate an API key in your Airtable account settings

## Usage

Run the script:
```bash
python get_new_listings_spinweb.py
```

## Onderhoud

To deactivate the virtual environment:
```bash
deactivate
```

To update the dependencies:
```bash
pip install -r requirements.txt --upgrade
```

## Updates

To pull the latest version:
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

- If Playwright errors, try reinstalling the browsers:
```bash
playwright install
```

- If Airtable errors, check if:
  - Your API key is correct
  - The Base ID is correct
  - The table "Listings" is named correctly
  - The column "Listing" is named correctly (case-sensitive)

- If OpenAI errors, check if:
  - Your API key is correct
  - You have enough credits

## Support

For questions or issues, contact the author via the above contact details.