import os
from dotenv import load_dotenv

# Load .env file for sensitive data
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Using PostgreSQL database for all storage

# PostgreSQL configuration
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")
PG_DATABASE = os.getenv("PG_DATABASE", "resumeai")

# Override PG_HOST if it's set to "db" and we're not in Docker
if PG_HOST == "db" and not os.path.exists("/.dockerenv"):
    PG_HOST = "localhost"

# Default prompt template
DEFAULT_PROMPT_TEMPLATE = """
Je bent een ervaren HR-specialist die helpt bij het evalueren van CV's voor vacatures.
Je taak is om een percentage match te bepalen tussen een CV en een vacature, 
waarbij 0% geen match is en 100% een perfecte match.

**Gewenste kwalificaties en vaardigheden:**
- Vereiste vaardigheden worden uit de functieomschrijving gehaald
- Optionele vaardigheden worden uit de functieomschrijving gehaald
- Ervaring in relevante sector wordt uit de functieomschrijving gehaald
- Vermogen om specifieke taken uit te voeren wordt uit de functieomschrijving gehaald
- Eventuele extra eisen worden uit de functieomschrijving gehaald

**Beoordelingscriteria:**
1. **Functieniveau vergelijking (ZEER BELANGRIJK):**
   - Vergelijk het niveau van de huidige functie met de vacature
   - Een stap terug in functieniveau is NIET wenselijk
   - Geef een negatief advies als de vacature een duidelijke stap terug is
   - Weeg dit zwaar mee in het matchpercentage
2. **Relevantie van werkervaring:** Hoe goed sluit de werkervaring van de kandidaat aan bij de functie? 
   - Is de ervaring **strategisch, operationeel of hands-on**?
3. **Vaardigheden match:** Heeft de kandidaat de vereiste vaardigheden en hoe sterk zijn ze aanwezig?
4. **Praktische inzetbaarheid:** Is de kandidaat direct inzetbaar of is er een leercurve?
5. **Risico's:** Zijn er risico's door gebrek aan specifieke ervaring, werkstijl of een te groot verschil met de functie?

**Uitvoer:**
- **Matchpercentage (0-100%)** op basis van hoe goed de kandidaat past bij de functie.
  Als de vacature een stap terug is in functieniveau, geef dan maximaal 40% match.
- **Sterke punten** van de kandidaat.
- **Zwakke punten** en aandachtspunten.
- **Eindoordeel** of de kandidaat geschikt is, met argumentatie.
  Begin het eindoordeel met een duidelijke analyse van het functieniveau verschil.

Geef ook een analyse van drie sterke punten en drie zwakke punten van de kandidaat in relatie tot de vacature.
Sluit af met een kort, helder eindoordeel over de geschiktheid van de kandidaat.

Vacature:
{vacancy_text}

CV:
{cv_text}

Je analyse moet de volgende structuur hebben (in het Nederlands):
```json
{{
  "name": "{name}",
  "percentage": [0-100],
  "sterke_punten": [
    "Punt 1",
    "Punt 2",
    "Punt 3"
  ],
  "zwakke_punten": [
    "Punt 1",
    "Punt 2",
    "Punt 3"
  ],
  "eindoordeel": "Je beknopte analyse en conclusie."
}}
```
Let op: je output moet een geldig JSON-object zijn, niet alleen de waarden.
"""

# Try to load prompt from file or environment variable
PROMPT_TEMPLATE = os.getenv("RESUME_PROMPT_TEMPLATE", DEFAULT_PROMPT_TEMPLATE)

# Project specific Spinweb.nl configuration
URL1_SPINWEB_USER = os.getenv("SPINWEB_USER")
URL1_SPINWEB_PASS = os.getenv("SPINWEB_PASS")
URL1_LOGIN_URL = "https://spinweb.nl/inloggen/form"
URL1_SOURCE = "https://spinweb.nl/interim-aanvragen?categories=ICT"
URL1_PROVIDER_NAME = "spinweb.nl"

# Project specific vector configuration
AI_MODEL = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-ada-002"

PDF_FOLDER = "app/resumes/"
POSTGRES_RESUME_TABLE = "resumes"  # PostgreSQL table name

# Matching configuration
MATCH_THRESHOLD = 0.75
MATCH_COUNT = 20
RESUME_RPC_FUNCTION_NAME = "match_resumes"  # PostgreSQL function name

# Client exclusion list
EXCLUDED_CLIENTS = os.getenv("EXCLUDED_CLIENTS", "").split(",") if os.getenv("EXCLUDED_CLIENTS") else []

