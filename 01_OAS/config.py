import os
from dotenv import load_dotenv

# Load .env file for sensitive data
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Project specific Spinweb.nl configuration
URL1_SPINWEB_USER = os.getenv("SPINWEB_USER")
URL1_SPINWEB_PASS = os.getenv("SPINWEB_PASS")
URL1_LOGIN_URL = "https://spinweb.nl/inloggen/form"
URL1_SOURCE = "https://spinweb.nl/interim-aanvragen?categories=ICT"
URL1_PROVIDER_NAME = "spinweb.nl"

# Project specific Airtable configuration
AIRTABLE_BASE_ID = "app6LNfGRTroZz2zA"
AIRTABLE_TABLE1 = "tblsbTQhmqndmIFan"
AIRTABLE_TABLE2 = "tblGRKanBz7PWWjtI"
#AIRTABLE_TABLE_NAME_AANVRAGEN = AIRTABLE_TABLE1
#AIRTABLE_TABLE_NAME_EXCLUDED = AIRTABLE_TABLE2

# Project specific vector configuration
EMBEDDING_MODEL = "text-embedding-ada-002"
#VECTOR_DIMENSIONS = 1536

# 1.ingest_resumes_supabase.py: Ingest configuration
PDF_FOLDER = "resumes/"
RESUME_VECTOR_TABLE = "01_OAS"

# 2.ingest_listings_spinweb_airtable.py: Ingest configuration

# 3.match_resumes_supabase.py: Match configuration
MATCH_THRESHOLD = 0.75
MATCH_COUNT = 20
RESUME_RPC_FUNCTION_NAME = "match_01_oas"


