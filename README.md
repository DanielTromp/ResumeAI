# ResumeAI
Find jobs and manage resumes powered by AI.

## Installatie

1. Clone de repository:
```bash
git clone https://github.com/yourusername/ResumeAI.git
cd ResumeAI
```

2. Maak en activeer een virtual environment:
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Installeer de dependencies:
```bash
pip install -r requirements.txt
```

4. Installeer Playwright browsers:
```bash
playwright install
```

## Configuratie

1. Maak een `.env` bestand aan in de root directory:
```env
OPENAI_API_KEY=jouw_openai_api_key
AIRTABLE_API_KEY=jouw_airtable_api_key
AIRTABLE_BASE_ID=jouw_base_id
SPINWEB_USERNAME=jouw_username
SPINWEB_PASSWORD=jouw_wachtwoord
```

2. Airtable setup:
   - Maak een nieuwe base aan
   - Maak een tabel genaamd "Listings"
   - Voeg een kolom toe genaamd "Listing" (type: Single line text)
   - Kopieer je Base ID (te vinden in de API documentatie)
   - Genereer een API key in je account settings

## Gebruik

Start het script:
```bash
python getNewListingsSpinweb.py
```

Het script zal:
- Inloggen op Spinweb
- Nieuwe vacatures ophalen
- De content verwerken met OpenAI
- De resultaten opslaan in Airtable

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

Bij vragen of problemen, open een issue op GitHub.