# Spinweb Vacancy Scraper

Een Python script dat automatisch vacatures van Spinweb ophaalt en naar Airtable uploadt.

## Over dit project

Dit script crawlt de Spinweb website om nieuwe vacatures te vinden en deze naar Airtable te uploaden.
Het voert de volgende taken uit:
1. Inloggen op Spinweb
2. Ophalen van nieuwe vacature listings
3. Vergelijken met bestaande listings in Airtable
4. Extractie van vacature details
5. Uploaden van nieuwe vacatures naar Airtable

**Metadata:**
- **Author:** Daniel Tromp
- **Email:** drpgmtromp@gmail.com
- **Version:** 1.0.0
- **Created:** 2025-02-11
- **Updated:** 2025-02-11
- **License:** MIT
- **Repository:** https://github.com/DanielTromp/ResumeAI

## Setup

1. Maak en activeer een virtual environment:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/MacOS
python3 -m venv venv
source venv/bin/activate
```

2. Installeer de vereiste packages:
```bash
pip install -r requirements.txt
```

3. Installeer Playwright browsers:
```bash
playwright install
```

4. Kopieer het `.env.example` bestand naar `.env`:
```bash
cp .env.example .env
```

5. Update het `.env` bestand met je eigen credentials:
```env
# OpenAI API configuratie
OPENAI_API_KEY=jouw_openai_api_key

# Airtable configuratie
AIRTABLE_API_KEY=jouw_airtable_api_key
AIRTABLE_BASE_ID=jouw_base_id
AIRTABLE_TABLE_NAME_PROCESSED=Aanvragen
AIRTABLE_TABLE_NAME_LISTINGS=Listings

# Spinweb configuratie
SPINWEB_USER=jouw_username
SPINWEB_PASS=jouw_wachtwoord
SOURCE_URL=jouw_gewenste_url
```

## Airtable Setup

1. Maak een nieuwe Airtable base aan
2. Maak twee tabellen:
   - `Aanvragen`: Voor nieuwe vacatures
     - Velden: URL (Text), Status (Single Select), Functie (Text), Klant (Text), Branche (Text), Regio (Text), Uren (Text), Tarief (Text), Geplaatst (Date), Sluiting (Date), Functieomschrijving (Long Text)
   - `Listings`: Voor verwerkte listings
     - Velden: Listing (Text)
3. Kopieer de Base ID uit de Airtable API documentatie
4. Genereer een API key in je Airtable account settings

## Gebruik

Run het script:
```bash
python get_new_listings_spinweb.py
```

## Onderhoud

Om de virtual environment te deactiveren:
```bash
deactivate
```

Om de dependencies te updaten:
```bash
pip install -r requirements.txt --upgrade
```

## Updates

Om de laatste versie op te halen:
```bash
# Bewaar lokale wijzigingen
git stash

# Haal updates op
git pull

# Pas lokale wijzigingen weer toe indien nodig
git stash pop

# Update dependencies indien nodig
pip install -r requirements.txt
```

## Troubleshooting

- Als Playwright errors geeft, probeer de browsers opnieuw te installeren:
```bash
playwright install
```

- Bij Airtable errors, controleer of:
  - Je API key correct is
  - De Base ID correct is
  - De tabel "Listings" heet
  - De kolom "Listing" heet (hoofdlettergevoelig)

- Bij OpenAI errors, controleer of:
  - Je API key correct is
  - Je voldoende credits hebt

## Support

Bij vragen of problemen, neem contact op met de auteur via de bovenstaande contactgegevens.