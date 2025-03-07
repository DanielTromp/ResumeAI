#!/usr/bin/env python3
"""
Combined Vacancy & Resume Matching Process

This script performs both the scraping of Spinweb vacancies and the matching 
    with resumes in a single integrated process:
1. Scraping of new Spinweb vacancies
2. Processing and saving in PostgreSQL
3. Matching CVs with new vacancies
4. Updating match results in PostgreSQL

Author: Daniel Tromp
Email: drpgmtromp@gmail.com
Version: 0.0.2
Created: 2025-02-25
Modified: 2025-02-26
License: MIT
Repository: https://github.com/DanielTromp/ResumeAI
"""

# Standard library imports
import json
import asyncio
import logging
import logging.handlers
from collections import defaultdict

# Third-party imports
import html2text
import tiktoken
import psycopg2
import psycopg2.extras
from openai import OpenAI
import playwright.async_api
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

# Project specific imports
from app.config import AI_MODEL, EMBEDDING_MODEL, OPENAI_API_KEY
from app.config import PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, PG_DATABASE
from app.config import URL1_SPINWEB_USER, URL1_SPINWEB_PASS
from app.config import URL1_PROVIDER_NAME, URL1_LOGIN_URL, URL1_SOURCE
from app.config import EXCLUDED_CLIENTS, MATCH_THRESHOLD, MATCH_COUNT
from app.config import RESUME_RPC_FUNCTION_NAME, PROMPT_TEMPLATE


# Configureer logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Changed to INFO to see more details

# Voeg een aparte handler toe voor voortgangsberichten
progress_handler = logging.StreamHandler()
progress_handler.setLevel(logging.INFO)
progress_formatter = logging.Formatter('%(message)s')
progress_handler.setFormatter(progress_formatter)

# Filter out FastAPI access logs
for name in logging.root.manager.loggerDict:
    if name.startswith('uvicorn.') or name.startswith('fastapi.'):
        logging.getLogger(name).setLevel(logging.WARNING)

# Maak een aparte logger voor voortgang
progress_logger = logging.getLogger('progress')
progress_logger.setLevel(logging.INFO)
progress_logger.addHandler(progress_handler)
progress_logger.propagate = False

# Initialize OpenAI client
client_openai = OpenAI(api_key=OPENAI_API_KEY)

# Initialize token calculator
enc = tiktoken.encoding_for_model(AI_MODEL)

# Import database service
from app.services.database_service import db_service

# Define a URL normalizer function
def normalize_url(url):
    """Normalize URL to a consistent format"""
    if not url:
        return ""
    # Strip protocol
    url = url.replace("https://", "").replace("http://", "")
    # Remove trailing slash
    if url.endswith("/"):
        url = url[:-1]
    return url

# Haal versie uit de docstring
SCRIPT_VERSION = "0.0.0"  # Default waarde
for line in __doc__.splitlines():
    if line.strip().startswith("Version:"):
        SCRIPT_VERSION = line.split("Version:")[1].strip()
        break

# HTML naar Markdown converter
def convert_html_to_markdown(html_text):
    """Convert HTML to Markdown while preserving the formatting."""
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = False
    converter.body_width = 0
    markdown_text = converter.handle(html_text)
    return markdown_text.strip()

def extract_data_from_html(html, url):
    """Extracts structured data from HTML and converts it to Markdown."""
    soup = BeautifulSoup(html, "html.parser")

    functie = soup.select_one(".title-page--text")
    klant = soup.select_one(".application-customer .dynamic-truncate")
    functieomschrijving = soup.select_one(".application-content")

    aanvraag_info = {}
    for item in soup.select(".application-info--item"):
        label = item.select_one(".application-info--label")
        value = item.select_one(".application-info--value")
        if label and value:
            aanvraag_info[label.get_text(strip=True)] = value.get_text(strip=True)

    markdown_output = "## Aanvraag Informatie\n"
    markdown_output += f"- [🔗 Aanvraag Link]({url})\n"
    markdown_output += "- **Functie:** " + (functie.get_text(strip=True) if functie else "Onbekend") + "\n"
    markdown_output += "- **Klant:** " + (klant.get_text(strip=True) if klant else "Onbekend") + "\n"
    for key, value in aanvraag_info.items():
        if key == "Uren":
            value = value.replace("onbekend", "").strip()
        markdown_output += f"- **{key}:** {value}\n"

    if functieomschrijving:
        # Get the entire HTML of the function description
        functieomschrijving_html = str(functieomschrijving)
    else:
        functieomschrijving_html = "<p>No description available.</p>"

    # Convert HTML to Markdown
    markdown_functieomschrijving = convert_html_to_markdown(functieomschrijving_html)

    markdown_output += "\n## Functieomschrijving\n" + markdown_functieomschrijving + "\n\n"

    return markdown_output

def check_environment_variables():
    """Checks if all required configuration variables are set."""
    required_vars = {
        'URL1_SPINWEB_USER': URL1_SPINWEB_USER,
        'URL1_SPINWEB_PASS': URL1_SPINWEB_PASS,
        'URL1_LOGIN_URL': URL1_LOGIN_URL,
        'URL1_PROVIDER_NAME': URL1_PROVIDER_NAME,
        'URL1_SOURCE': URL1_SOURCE,
        'OPENAI_API_KEY': OPENAI_API_KEY,
        'PG_HOST': PG_HOST,
        'PG_PORT': PG_PORT,
        'PG_USER': PG_USER,
        'PG_PASSWORD': PG_PASSWORD,
        'PG_DATABASE': PG_DATABASE
    }

    missing_vars = [name for name, value in required_vars.items()
                   if not value or value.strip() == '']

    if missing_vars:
        error_msg = (
            "\n\nMissing or empty configuration variables found:\n"
            f"{', '.join(missing_vars)}\n"
            "\nCheck if these variables are correctly set in config.py"
        )
        raise ValueError(error_msg)

def get_embedding(text: str) -> list[float]:
    """Genereer een embedding voor de gegeven tekst via OpenAI's API."""
    embedding_response = client_openai.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL
    )
    return embedding_response.data[0].embedding

def evaluate_candidate(name: str, cv_text: str, vacancy_text: str) -> tuple[dict, dict]:
    """Evalueer een kandidaat CV tegen een vacature tekst met AI_MODEL (GPT-4o-mini)."""
    # Use the prompt template from config, filling in the placeholders
    prompt = PROMPT_TEMPLATE.format(
        name=name,
        vacancy_text=vacancy_text,
        cv_text=cv_text
    )

    # Bereken tokens
    input_tokens = len(enc.encode(prompt))

    try:
        response = client_openai.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "Je bent een AI die sollicitanten evalueert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        output_tokens = response.usage.completion_tokens
        result_text = response.choices[0].message.content.strip()

        # Extract JSON from the response if needed
        if "```json" in result_text:
            json_str = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            json_str = result_text.split("```")[1].strip()
        else:
            json_str = result_text

        # Clean and parse
        json_str = json_str.replace('\n', ' ').replace('\\', '\\\\')
        evaluation = json.loads(json_str)

        token_usage = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens
        }

        return evaluation, token_usage
    except Exception as e:
        logger.error(f"⚠️ Error in evaluate_candidate: {str(e)}")
        # Return fallback evaluation
        evaluation = {
            "name": name,
            "percentage": 0,
            "sterke_punten": ["Evaluatie mislukt"],
            "zwakke_punten": ["Evaluatie mislukt"],
            "eindoordeel": f"Evaluatie kon niet worden voltooid vanwege een fout: {str(e)}"
        }
        token_usage = {"input_tokens": input_tokens, "output_tokens": 0, "total_tokens": input_tokens}
        return evaluation, token_usage

def process_vacancy(vacancy_id: str, vacancy_text: str, matches: dict) -> tuple[dict, dict]:
    """Verwerkt één vacature en evalueert alle kandidaten."""
    progress_logger.info(f"\n📊 Start evaluatie van {len(matches)} kandidaten voor vacature {vacancy_id}")

    all_evaluations = []
    token_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "evaluations_count": 0}

    for name, chunks in matches.items():
        progress_logger.info(f"  👤 Evalueren van kandidaat: {name}")
        cv_text = " ".join(chunks)
        evaluation, tokens = evaluate_candidate(name, cv_text, vacancy_text)
        all_evaluations.append(evaluation)
        token_usage["input_tokens"] += tokens["input_tokens"]
        token_usage["output_tokens"] += tokens["output_tokens"]
        token_usage["total_tokens"] += tokens["total_tokens"]
        token_usage["evaluations_count"] += 1
        progress_logger.info(f"    ✓ Match percentage: {evaluation['percentage']}%")

    sorted_evaluations = sorted(all_evaluations, key=lambda x: x["percentage"], reverse=True)
    top_evaluations = sorted_evaluations[:5]
    best_match = top_evaluations[0] if top_evaluations else None

    if best_match:
        new_status = "Open" if best_match["percentage"] >= 60 else "AI afgewezen"
        # Create a payload with all relevant data
        results = {
            "Status": new_status,
            "Checked_resumes": ", ".join(eval["name"] for eval in top_evaluations),
            "Top_Match": best_match["percentage"],
            "Match Toelichting": json.dumps({
                "beste_match": best_match,
                "alle_matches": top_evaluations,
                "token_usage": token_usage
            }, ensure_ascii=False, indent=2)
        }
        return results, token_usage
    return None, token_usage

async def spider_vacatures():
    """
    Spider functie voor het scrapen en verwerken van Spinweb vacatures.
    Haalt vacatures op, doet de CV matching en slaat alles in één keer op.
    """
    progress_logger.info("🔍 Start gecombineerd vacature ophalen & matching process")

    # Note: Cleanup of closed listings now handled via PostgreSQL
    try:
        # Connect to PostgreSQL and mark old listings as closed
        from app.db_init import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        
        # Update listings older than 30 days to "Gesloten"
        cursor.execute(
            """
            UPDATE vacancies 
            SET status = 'Gesloten', updated_at = NOW()
            WHERE created_at < NOW() - INTERVAL '30 days' 
            AND status NOT IN ('Gesloten', 'Geplaatst', 'Afgezegd')
            """
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        progress_logger.info("✅ Cleanup of old listings complete")
    except Exception as e:
        progress_logger.error(f"❌ Error during cleanup of old listings: {str(e)}")

    # Configure the crawler
    browser_config = BrowserConfig(
        headless=True,
        verbose=True
    )

    crawler_run_config = CrawlerRunConfig(
        js_code="window.scrollTo(0, document.body.scrollHeight);",
        wait_for="body",
        cache_mode=CacheMode.BYPASS
    )

    crawler = AsyncWebCrawler(config=browser_config, request_timeout=30000)

    # Log crawler events via hook
    async def on_page_context_created(page: playwright.async_api.Page, 
                                      browser_context: playwright.async_api.BrowserContext = None,
                                      **kwargs):
        """Hook for setting up the page and context after creation."""
        progress_logger.info("[HOOK] Setting up page & context.")
        try:
            await page.goto(URL1_LOGIN_URL, timeout=10000)
        except playwright.async_api.TimeoutError as e:
            progress_logger.error("Timeout loading login page: %s", e)
            return page
        except playwright.async_api.Error as e:
            progress_logger.error("Playwright error loading login page: %s", e)
            return page

        try:
            if await page.is_visible("input[name='user']"):
                progress_logger.info("Logging in...")
                await page.fill("input[name='user']", URL1_SPINWEB_USER)
                await page.fill("input[name='pass']", URL1_SPINWEB_PASS)
                await page.click("button[type='submit']")
                await page.wait_for_load_state("networkidle", timeout=30000)
            else:
                progress_logger.info("Already logged in, skipping login step.")
        except playwright.async_api.TimeoutError as e:
            progress_logger.error("Timeout during login process: %s", e)
        except playwright.async_api.Error as e:
            progress_logger.error("Playwright error during login: %s", e)

        return page

    crawler.crawler_strategy.set_hook("on_page_context_created", on_page_context_created)

    await crawler.start()

    if not URL1_SOURCE:
        progress_logger.error("Error: No source URL configured in environment variables.")
        return []

    result = await crawler.arun(URL1_SOURCE, config=crawler_run_config)

    if not result.success:
        progress_logger.error("Error crawling source URL: %s", result.error_message)
        await crawler.close()
        return
    
    progress_logger.info("Crawled URL: %s", result.url)
    soup = BeautifulSoup(result.html, 'html.parser')

    # Zoek alle vacature links
    vacancy_links = set()
    for link in soup.find_all('a', href=True):
        href = link['href']
        if '/aanvraag/' in href:
            # Zorg voor volledige URLs met protocol voor de crawler
            full_url = f"https://{URL1_PROVIDER_NAME}{href}" if href.startswith('/') else href
            if not full_url.startswith('http'):
                full_url = f"https://{full_url}"
            vacancy_links.add(full_url)

    progress_logger.info(f"Found {len(vacancy_links)} vacancy links")

    # URL normalisatie voor database en crawler
    # Voor database: zonder protocol (spinweb.nl/aanvraag/123)
    # Voor crawler: met protocol (https://spinweb.nl/aanvraag/123)
    vacancy_links_db = {normalize_url(link) for link in vacancy_links}
    vacancy_links_crawler = {link for link in vacancy_links}  # Behoud originele URLs met protocol

    # Maak een mapping van database URLs naar crawler URLs
    vacancy_links_map = {}
    for link in vacancy_links:
        db_url = normalize_url(link)
        vacancy_links_map[db_url] = link  # Gebruik originele URL met protocol voor crawler

    # Get existing vacancy URLs from PostgreSQL
    try:
        from app.db_init import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT url FROM vacancies")
        existing_rows = cursor.fetchall()
        existing_aanvragen_urls = {normalize_url(row[0]) for row in existing_rows if row[0]}
        cursor.close()
        conn.close()
        progress_logger.info(f"Found {len(existing_aanvragen_urls)} existing listings in database")
    except Exception as e:
        progress_logger.error(f"Error retrieving existing listings: {str(e)}")
        existing_aanvragen_urls = set()
        
    # Get lowest URL (oldest vacancy) as a cutoff point
    try:
        from app.db_init import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT url FROM vacancies ORDER BY created_at ASC LIMIT 1")
        result = cursor.fetchone()
        lowest_url = normalize_url(result[0]) if result and result[0] else ""
        cursor.close()
        conn.close()
    except Exception as e:
        progress_logger.error(f"Error retrieving oldest listing: {str(e)}")
        lowest_url = ""

    # Filter new listings (genormaliseerde URLs zonder protocol)
    new_listings_db = {link for link in vacancy_links_db
                    if link not in existing_aanvragen_urls and link > lowest_url}
    new_listings_db = sorted(new_listings_db)

    # Sorteer de crawler-vriendelijke URLs in dezelfde volgorde
    new_listings_crawler = []
    for db_url in new_listings_db:
        if db_url in vacancy_links_map:
            new_listings_crawler.append(vacancy_links_map[db_url])
        else:
            # Fallback: als de URL niet in de mapping staat, voeg het protocol toe
            crawler_url = "https://" + db_url
            new_listings_crawler.append(crawler_url)
            progress_logger.warning(f"URL {db_url} niet gevonden in mapping, fallback gebruikt: {crawler_url}")

    progress_logger.info(f"Found {len(new_listings_db)} new vacancies to process")

    # Verwerk elke nieuwe vacature: ophalen, matchen, en dan pas opslaan
    excluded_clients = EXCLUDED_CLIENTS
    if isinstance(excluded_clients, str):
        excluded_clients = [client.strip() for client in excluded_clients.split(',') if client.strip()]
    elif not isinstance(excluded_clients, list):
        excluded_clients = []
    progress_logger.info(f"ℹ️ Uitgesloten klanten geladen: {len(excluded_clients)}")
    total_token_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "total_evaluations": 0}

    for i, db_url in enumerate(new_listings_db):
        crawler_url = new_listings_crawler[i]
        progress_logger.info(f"\n=== Verwerken vacature {i+1}/{len(new_listings_db)} ===")

        # Stap 1: Vacature details ophalen
        try:
            result = await crawler.arun(crawler_url, config=crawler_run_config)
            if not result.success:
                progress_logger.error(f"Error crawling {crawler_url}: {result.error_message}")
                continue

            progress_logger.info(f"Succesvol gecrawled: {crawler_url}")
            markdown_data = extract_data_from_html(result.html, db_url)
            
            # Function to parse markdown data into structured format
            def parse_markdown_data(markdown, url):
                """Parse Markdown data into a structured dictionary"""
                data = {
                    "Url": url,
                    "Functie": "",
                    "Klant": "",
                    "Functieomschrijving": "",
                    "Status": "Nieuw",
                    "Branche": "",
                    "Regio": "",
                    "Uren": "",
                    "Tarief": "",
                    "Geplaatst": None,
                    "Sluiting": None
                }
                
                # Parse lines
                lines = markdown.splitlines()
                in_functieomschrijving = False
                func_beschrijving = []
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    if line.startswith("## Functieomschrijving"):
                        in_functieomschrijving = True
                        continue
                        
                    if in_functieomschrijving:
                        func_beschrijving.append(line)
                        continue
                        
                    if line.startswith("- **Functie:**"):
                        data["Functie"] = line.replace("- **Functie:**", "").strip()
                    elif line.startswith("- **Klant:**"):
                        data["Klant"] = line.replace("- **Klant:**", "").strip()
                    elif line.startswith("- **Branche:**"):
                        data["Branche"] = line.replace("- **Branche:**", "").strip()
                    elif line.startswith("- **Regio:**"):
                        data["Regio"] = line.replace("- **Regio:**", "").strip()
                    elif line.startswith("- **Uren:**"):
                        data["Uren"] = line.replace("- **Uren:**", "").strip()
                    elif line.startswith("- **Tarief:**"):
                        data["Tarief"] = line.replace("- **Tarief:**", "").strip()
                    elif line.startswith("- **Geplaatst:**"):
                        data["Geplaatst"] = line.replace("- **Geplaatst:**", "").strip()
                    elif line.startswith("- **Sluitingsdatum:**"):
                        data["Sluiting"] = line.replace("- **Sluitingsdatum:**", "").strip()
                
                # Join the function description
                data["Functieomschrijving"] = "\n".join(func_beschrijving)
                
                return data
                
            vacancy_data = parse_markdown_data(markdown_data, db_url)
            
            # Voeg Model en Version toe aan de vacature data
            vacancy_data["Model"] = AI_MODEL
            vacancy_data["Version"] = SCRIPT_VERSION

            # Check of de klant op de uitsluitlijst staat
            client_name = vacancy_data.get("Klant", "").strip()
            if client_name in excluded_clients:
                progress_logger.info(f"⏭️ Klant '{client_name}' staat op de uitsluitlijst; markeer als AI afgewezen.")
                
                # Update PostgreSQL directly
                try:
                    from app.db_init import get_connection
                    conn = get_connection()
                    cursor = conn.cursor()
                    
                    # Check if vacancy already exists
                    cursor.execute("SELECT id FROM vacancies WHERE url = %s", (db_url,))
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Update existing record
                        cursor.execute(
                            """
                            UPDATE vacancies 
                            SET status = 'AI afgewezen',
                                checked_resumes = '',
                                top_match = 0,
                                match_toelichting = %s,
                                updated_at = NOW()
                            WHERE url = %s
                            """,
                            (json.dumps({"reason": "Klant staat op de uitsluitlijst"}), db_url)
                        )
                    else:
                        # Insert new record
                        cursor.execute(
                            """
                            INSERT INTO vacancies (
                                url, functie, klant, functieomschrijving, status,
                                branche, regio, uren, tarief, 
                                checked_resumes, top_match, match_toelichting,
                                model, version, created_at, updated_at
                            ) VALUES (
                                %s, %s, %s, %s, %s,
                                %s, %s, %s, %s,
                                %s, %s, %s,
                                %s, %s, NOW(), NOW()
                            )
                            """,
                            (
                                db_url,
                                vacancy_data.get("Functie", ""),
                                vacancy_data.get("Klant", ""),
                                vacancy_data.get("Functieomschrijving", ""),
                                "AI afgewezen",
                                vacancy_data.get("Branche", ""),
                                vacancy_data.get("Regio", ""),
                                vacancy_data.get("Uren", ""),
                                vacancy_data.get("Tarief", ""),
                                "",
                                0,
                                json.dumps({"reason": "Klant staat op de uitsluitlijst"}),
                                vacancy_data.get("Model", ""),
                                vacancy_data.get("Version", "")
                            )
                        )
                    
                    conn.commit()
                    cursor.close()
                    conn.close()
                    progress_logger.info(f"✅ Vacancy for excluded client saved to PostgreSQL")
                except Exception as e:
                    progress_logger.error(f"❌ Error saving excluded client vacancy: {str(e)}")
                    if 'conn' in locals() and conn:
                        conn.rollback()
                        conn.close()
                        
                continue

            # Stap 2: CV matching uitvoeren
            vacancy_text = vacancy_data.get("Functieomschrijving", "")
            if not vacancy_text:
                progress_logger.warning(f"⚠️ Geen functiebeschrijving gevonden voor {db_url}, markeren als 'AI afgewezen'.")
                vacancy_data["Status"] = "AI afgewezen"
                
                # Update PostgreSQL with rejection status
                try:
                    from app.db_init import get_connection
                    pg_conn = get_connection()
                    pg_cursor = pg_conn.cursor()
                    
                    # Check if vacancy already exists
                    pg_cursor.execute("SELECT id FROM vacancies WHERE url = %s", (db_url,))
                    existing = pg_cursor.fetchone()
                    
                    if existing:
                        # Update existing record
                        pg_cursor.execute(
                            """
                            UPDATE vacancies 
                            SET status = 'AI afgewezen',
                                checked_resumes = '',
                                top_match = 0,
                                match_toelichting = %s,
                                updated_at = NOW()
                            WHERE url = %s
                            """,
                            (json.dumps({"reason": "Geen functiebeschrijving gevonden"}), db_url)
                        )
                    else:
                        # Insert new record with AI afgewezen status
                        pg_cursor.execute(
                            """
                            INSERT INTO vacancies (
                                url, functie, klant, status, branche, regio, uren, tarief, 
                                checked_resumes, top_match, match_toelichting, model, version,
                                created_at, updated_at
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s,
                                '', 0, %s, %s, %s,
                                NOW(), NOW()
                            )
                            """,
                            (
                                db_url,
                                vacancy_data.get("Functie", ""),
                                vacancy_data.get("Klant", ""),
                                "AI afgewezen",
                                vacancy_data.get("Branche", ""),
                                vacancy_data.get("Regio", ""),
                                vacancy_data.get("Uren", ""),
                                vacancy_data.get("Tarief", ""),
                                json.dumps({"reason": "Geen functiebeschrijving gevonden"}),
                                vacancy_data.get("Model", ""),
                                vacancy_data.get("Version", "")
                            )
                        )
                    
                    pg_conn.commit()
                    pg_cursor.close()
                    pg_conn.close()
                    progress_logger.info(f"✅ Vacancy without function description marked as AI afgewezen in PostgreSQL")
                except Exception as pg_error:
                    progress_logger.error(f"❌ Error saving rejection status for vacancy without description: {str(pg_error)}")
                    if 'pg_conn' in locals() and pg_conn:
                        pg_conn.rollback()
                        pg_conn.close()
                        
                # Now we can skip to the next vacancy
                continue

            # Genereer embedding en zoek matches
            progress_logger.info(f"Genereren embedding en zoeken naar CV matches...")
            vacancy_embedding = get_embedding(vacancy_text)
            
            # Debug info about the embedding
            progress_logger.info(f"Embedding generated: length={len(vacancy_embedding)}")
            progress_logger.info("Using PostgreSQL database")
            
            # Save vacancy data to PostgreSQL first
            try:
                # Create connection to PostgreSQL
                from app.db_init import get_connection
                conn = get_connection()
                cursor = conn.cursor()
                
                # Check if vacancy already exists in PostgreSQL
                cursor.execute(
                    """
                    SELECT id FROM vacancies WHERE url = %s
                    """,
                    (db_url,)
                )
                existing_vacancy = cursor.fetchone()
                
                if existing_vacancy:
                    # Update existing vacancy
                    vacancy_id = existing_vacancy[0]
                    progress_logger.info(f"Updating existing vacancy in PostgreSQL (ID: {vacancy_id})")
                    cursor.execute(
                        """
                        UPDATE vacancies 
                        SET functie = %s, 
                            klant = %s, 
                            functieomschrijving = %s, 
                            status = %s,
                            updated_at = NOW()
                        WHERE id = %s
                        """,
                        (
                            vacancy_data.get("Functie", ""),
                            vacancy_data.get("Klant", ""),
                            vacancy_data.get("Functieomschrijving", ""),
                            vacancy_data.get("Status", "Nieuw"),
                            vacancy_id
                        )
                    )
                else:
                    # Insert new vacancy
                    progress_logger.info(f"Inserting new vacancy into PostgreSQL")
                    try:
                        # Get all columns from vacancy_data that might need to be inserted
                        cursor.execute(
                            """
                            INSERT INTO vacancies (
                                url, functie, klant, functieomschrijving, status, 
                                branche, regio, uren, tarief, checked_resumes, 
                                geplaatst, sluiting, external_id, model, version,
                                created_at, updated_at
                            ) 
                            VALUES (
                                %s, %s, %s, %s, %s, 
                                %s, %s, %s, %s, %s, 
                                %s, %s, %s, %s, %s,
                                NOW(), NOW()
                            )
                            RETURNING id
                            """,
                            (
                                db_url,
                                vacancy_data.get("Functie", ""),
                                vacancy_data.get("Klant", ""),
                                vacancy_data.get("Functieomschrijving", ""),
                                vacancy_data.get("Status", "Nieuw"),
                                vacancy_data.get("Branche", ""),
                                vacancy_data.get("Regio", ""),
                                vacancy_data.get("Uren", ""),
                                vacancy_data.get("Tarief", ""),
                                vacancy_data.get("Checked_resumes", ""),
                                None if not vacancy_data.get("Geplaatst") else vacancy_data.get("Geplaatst"),
                                None if not vacancy_data.get("Sluiting") else vacancy_data.get("Sluiting"),
                                vacancy_data.get("External_id", ""),
                                vacancy_data.get("Model", ""),
                                vacancy_data.get("Version", "")
                            )
                        )
                    except Exception as insert_error:
                        progress_logger.error(f"Error in full insert, trying minimal insert: {str(insert_error)}")
                        # Fallback to minimal insert if the full insert fails
                        cursor.execute(
                            """
                            INSERT INTO vacancies (url, functie, klant, functieomschrijving, status, created_at, updated_at) 
                            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                            RETURNING id
                            """,
                            (
                                db_url,
                                vacancy_data.get("Functie", ""),
                                vacancy_data.get("Klant", ""),
                                vacancy_data.get("Functieomschrijving", ""),
                                vacancy_data.get("Status", "Nieuw")
                            )
                        )
                    vacancy_id = cursor.fetchone()[0]
                
                # Commit the transaction
                conn.commit()
                cursor.close()
                conn.close()
                
                progress_logger.info(f"Vacancy saved to PostgreSQL with ID: {vacancy_id}")
            except Exception as pg_error:
                progress_logger.error(f"Failed to save vacancy to PostgreSQL: {str(pg_error)}")
                if 'conn' in locals() and conn:
                    conn.rollback()
                    conn.close()
            
            try:
                # Get matches using the database service
                query_data = db_service.get_vector_matches(
                    embedding=vacancy_embedding,
                    threshold=MATCH_THRESHOLD,
                    count=MATCH_COUNT
                )
                
                progress_logger.info(f"Query returned {len(query_data) if query_data else 0} results")

                if not query_data:
                    progress_logger.warning(f"⚠️ Geen CV matches gevonden")
                    vacancy_data["Status"] = "AI afgewezen"
                    vacancy_data["Checked_resumes"] = ""
                    vacancy_data["Top_Match"] = 0
                    vacancy_data["Match Toelichting"] = "Geen matches gevonden"
                    
                    # Update PostgreSQL with rejection status
                    try:
                        from app.db_init import get_connection
                        pg_conn = get_connection()
                        pg_cursor = pg_conn.cursor()
                        
                        pg_cursor.execute(
                            """
                            UPDATE vacancies 
                            SET status = 'AI afgewezen',
                                top_match = 0,
                                match_toelichting = %s,
                                checked_resumes = '',
                                updated_at = NOW()
                            WHERE url = %s
                            """,
                            (
                                json.dumps({"reason": "Geen matches gevonden"}),
                                db_url
                            )
                        )
                        pg_conn.commit()
                        pg_cursor.close()
                        pg_conn.close()
                        progress_logger.info(f"Rejection status saved to PostgreSQL for {db_url}")
                    except Exception as pg_error:
                        progress_logger.error(f"Failed to update rejection status in PostgreSQL: {str(pg_error)}")
                        if 'pg_conn' in locals() and pg_conn:
                            pg_conn.rollback()
                            pg_conn.close()
                            
                    # Already saved to PostgreSQL above
                    continue

                # Verwerk matches
                matches = defaultdict(list)
                for item in query_data:
                    matches[item["name"]].append(item["cv_chunk"])

                progress_logger.info(f"📝 {len(matches)} kandidaten gevonden voor evaluatie")
                match_results, vacancy_tokens = process_vacancy(0, vacancy_text, matches)  # 0 is dummy ID

                total_token_usage["input_tokens"] += vacancy_tokens["input_tokens"]
                total_token_usage["output_tokens"] += vacancy_tokens["output_tokens"]
                total_token_usage["total_tokens"] += vacancy_tokens["total_tokens"]
                total_token_usage["total_evaluations"] += vacancy_tokens["evaluations_count"]

                if match_results:
                    # Update de vacature data met match resultaten
                    vacancy_data.update(match_results)
                    progress_logger.info(f"Match resultaten toegevoegd aan vacature data")
                    
                    # Also update PostgreSQL with match results
                    try:
                        from app.db_init import get_connection
                        pg_conn = get_connection()
                        pg_cursor = pg_conn.cursor()
                        
                        # Store match details in PostgreSQL
                        pg_cursor.execute(
                            """
                            UPDATE vacancies 
                            SET status = %s,
                                top_match = %s,
                                match_toelichting = %s,
                                checked_resumes = %s,
                                updated_at = NOW()
                            WHERE url = %s
                            """,
                            (
                                match_results.get("Status", "AI afgewezen"),
                                match_results.get("Top_Match", 0),
                                json.dumps(match_results.get("Match Toelichting", "{}")),
                                match_results.get("Checked_resumes", ""),
                                db_url
                            )
                        )
                        pg_conn.commit()
                        pg_cursor.close()
                        pg_conn.close()
                        progress_logger.info(f"Match results saved to PostgreSQL for {db_url}")
                    except Exception as pg_error:
                        progress_logger.error(f"Failed to update match results in PostgreSQL: {str(pg_error)}")
                        if 'pg_conn' in locals() and pg_conn:
                            pg_conn.rollback()
                            pg_conn.close()
                else:
                    progress_logger.warning(f"⚠️ Geen match resultaten gegenereerd")
                    vacancy_data["Status"] = "AI afgewezen"
                    vacancy_data["Checked_resumes"] = ""
                    vacancy_data["Top_Match"] = 0
                    vacancy_data["Match Toelichting"] = "Geen resultaten gegenereerd"
                    
                    # Update PostgreSQL with rejection status
                    try:
                        from app.db_init import get_connection
                        pg_conn = get_connection()
                        pg_cursor = pg_conn.cursor()
                        
                        pg_cursor.execute(
                            """
                            UPDATE vacancies 
                            SET status = 'AI afgewezen',
                                top_match = 0,
                                match_toelichting = %s,
                                checked_resumes = '',
                                updated_at = NOW()
                            WHERE url = %s
                            """,
                            (
                                json.dumps({"reason": "Geen resultaten gegenereerd"}),
                                db_url
                            )
                        )
                        pg_conn.commit()
                        pg_cursor.close()
                        pg_conn.close()
                    except Exception as pg_error:
                        progress_logger.error(f"Failed to update rejection status in PostgreSQL: {str(pg_error)}")
                        if 'pg_conn' in locals() and pg_conn:
                            pg_conn.rollback()
                            pg_conn.close()

            except (psycopg2.Error, Exception) as e:
                progress_logger.error(f"⚠️ Fout bij CV matching: {str(e)}", exc_info=True)
                vacancy_data["Status"] = "Nieuw"  # Changed from Error to Nieuw which is a valid status
                vacancy_data["Checked_resumes"] = ""
                vacancy_data["Top_Match"] = 0
                vacancy_data["Match Toelichting"] = f"Fout tijdens matching: {str(e)[:100]}"

            # Step 3: Save all data (already saved to PostgreSQL during processing)
            progress_logger.info(f"✅ Vacature {db_url} is succesvol verwerkt en opgeslagen in PostgreSQL")

        except Exception as e:
            progress_logger.error(f"⚠️ Onverwachte fout bij verwerken vacature {db_url}: {str(e)}", exc_info=True)

    await crawler.close()

    # Eindrapport
    progress_logger.info("\n🚀 Alle vacatures verwerkt!")
    progress_logger.info("\n📈 Eindrapport token gebruik:")
    progress_logger.info(f"Totaal aantal evaluaties: {total_token_usage['total_evaluations']}")
    if total_token_usage['total_evaluations'] > 0:
        avg = total_token_usage['total_tokens'] / total_token_usage['total_evaluations']
        progress_logger.info(f"Gemiddeld tokens per evaluatie: {avg:.2f}")

# Removed test_database_with_dummy_data function since we now use the db_init module

async def main():
    """Main function voor het volledige proces."""
    try:
        # Check environment variables
        check_environment_variables()
        
        # Test PostgreSQL connection and set up test data
        try:
            # Import database functions
            from app.db_init import get_connection, initialize_database, add_test_data
            
            # Test connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            progress_logger.info("✅ PostgreSQL connection successful")
            
            # Initialize database and insert test data if needed
            initialize_database()
            add_test_data()
        except Exception as e:
            progress_logger.error(f"❌ PostgreSQL connection failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return

        # Voer het gecombineerde proces uit in één stap
        progress_logger.info("🚀 Start gecombineerd vacature & CV match proces")
        await spider_vacatures()

        progress_logger.info("✅ Volledig proces succesvol afgerond!")
    except Exception as e:
        progress_logger.error(f"❌ Fout in het gecombineerde proces: {str(e)}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())

# End of file
