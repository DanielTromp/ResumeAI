import os
from dotenv import load_dotenv

# Load .env file for sensitive data
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Project specific Spinweb.nl configuration
URL1_SPINWEB_USER = os.getenv("SPINWEB_USER")
URL1_SPINWEB_PASS = os.getenv("SPINWEB_PASS")
URL1_LOGIN_URL = "https://spinweb.nl/inloggen/form"
URL1_SOURCE = "https://spinweb.nl/interim-aanvragen?categories=ICT"
URL1_PROVIDER_NAME = "spinweb.nl"

# Project specific vector configuration
EMBEDDING_MODEL = "text-embedding-ada-002"

PDF_FOLDER = "resumes/"
RESUME_VECTOR_TABLE = "01_OAS"

# Nocodb configuration
NOCODB_URL = os.getenv("NOCODB_URL")
NOCODB_TOKEN = os.getenv("NOCODB_TOKEN")
NOCODB_PROJECT = os.getenv("NOCODB_PROJECT")
NOCODB_TABLE = os.getenv("NOCODB_TABLE")

MATCH_THRESHOLD = 0.75
MATCH_COUNT = 20
RESUME_RPC_FUNCTION_NAME = "match_01_oas"
EXCLUDED_CLIENTS = os.getenv("EXCLUDED_CLIENTS")

