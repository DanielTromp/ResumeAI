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
Version: 0.0.4
Created: 2025-02-25
Modified: 2025-03-10
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

# Project specific imports - using the centralized configuration system
from app.config import config
# Import individual variables for backward compatibility
from app.config import (
    AI_MODEL, EMBEDDING_MODEL, OPENAI_API_KEY,
    PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, PG_DATABASE,
    URL1_SPINWEB_USER, URL1_SPINWEB_PASS,
    URL1_PROVIDER_NAME, URL1_LOGIN_URL, URL1_SOURCE,
    EXCLUDED_CLIENTS, MATCH_THRESHOLD, MATCH_COUNT,
    RESUME_RPC_FUNCTION_NAME, PROMPT_TEMPLATE
)


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

# Import services
from app.services.database_service import db_service
from app.services.email_service import email_service

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
    progress_logger.info(f"Extracting data from HTML for URL: {url}")
    
    # Save HTML for debugging
    try:
        import os
        debug_dir = os.path.join(os.getcwd(), "debug")
        os.makedirs(debug_dir, exist_ok=True)
        
        # Use a URL-based filename to avoid collisions
        url_part = url.replace("https://", "").replace("http://", "").replace("/", "_").replace(".", "_")
        with open(os.path.join(debug_dir, f"vacancy_{url_part}.html"), "w") as f:
            f.write(html)
        progress_logger.info(f"✅ Saved vacancy HTML to debug/vacancy_{url_part}.html")
    except Exception as e:
        progress_logger.error(f"Could not save vacancy HTML: {str(e)}")
    
    soup = BeautifulSoup(html, "html.parser")
    
    # Log the title of the page to verify we're on a vacancy page
    page_title = soup.title.string if soup.title else "No title found"
    progress_logger.info(f"Page title: {page_title}")
    
    # Try multiple possible selectors for each field to be more robust
    # Log which selector was found for debugging
    
    # Find job title
    functie = None
    job_title_selectors = [
        ".title-page--text",            # Original selector
        "h1",                          # Generic - first h1
        ".job-title",                  # Common class name
        ".vacancy-title"               # Common class name
    ]
    for selector in job_title_selectors:
        element = soup.select_one(selector)
        if element:
            functie = element
            progress_logger.info(f"Found job title using selector: {selector}")
            break
    
    # Find client name
    klant = None
    client_selectors = [
        ".application-customer .dynamic-truncate",  # Original
        ".customer-name",                          # Common
        ".client-name",                            # Common
        ".company-name"                            # Common
    ]
    for selector in client_selectors:
        element = soup.select_one(selector)
        if element:
            klant = element
            progress_logger.info(f"Found client using selector: {selector}")
            break
            
    # As a fallback for client name, look for text near "Klant:" or "Opdrachtgever:"
    if not klant:
        for element in soup.find_all(string=lambda text: "klant:" in text.lower() or "opdrachtgever:" in text.lower()):
            parent = element.parent
            next_element = parent.next_sibling
            if next_element:
                klant_text = next_element.get_text(strip=True)
                klant = type('obj', (object,), {'get_text': lambda self, strip=False: klant_text})
                progress_logger.info(f"Found client using text search: {klant_text}")
                break
    
    # Find job description
    functieomschrijving = None
    description_selectors = [
        ".application-content",       # Original
        ".job-description",           # Common
        ".vacancy-description",       # Common
        ".description"                # Generic
    ]
    for selector in description_selectors:
        element = soup.select_one(selector)
        if element:
            functieomschrijving = element
            progress_logger.info(f"Found job description using selector: {selector}")
            break
    
    # If no job description found, try to get the main content
    if not functieomschrijving:
        # Try to find the largest text block on the page
        text_blocks = []
        for tag in soup.find_all(["div", "section", "article"]):
            if tag.get_text(strip=True):
                text_blocks.append((tag, len(tag.get_text(strip=True))))
        
        if text_blocks:
            # Get the block with the most text
            largest_block = max(text_blocks, key=lambda x: x[1])
            functieomschrijving = largest_block[0]
            progress_logger.info(f"Found job description using largest text block: {largest_block[1]} chars")
            
    # Parse additional info - first the original way
    aanvraag_info = {}
    info_items = soup.select(".application-info--item")
    if info_items:
        progress_logger.info(f"Found {len(info_items)} info items using original selector")
        for item in info_items:
            label = item.select_one(".application-info--label")
            value = item.select_one(".application-info--value")
            if label and value:
                key = label.get_text(strip=True)
                val = value.get_text(strip=True)
                aanvraag_info[key] = val
    
    # Fallback: look for any structured info in tables or definition lists
    if not aanvraag_info:
        # Try tables
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cells = row.find_all(["th", "td"])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    val = cells[1].get_text(strip=True)
                    if key and val:
                        aanvraag_info[key] = val
        
        # Try definition lists
        for dl in soup.find_all("dl"):
            terms = dl.find_all("dt")
            defs = dl.find_all("dd")
            for i in range(min(len(terms), len(defs))):
                key = terms[i].get_text(strip=True)
                val = defs[i].get_text(strip=True)
                if key and val:
                    aanvraag_info[key] = val
    
    # Log what we found
    progress_logger.info(f"Found job title: {functie.get_text(strip=True) if functie else 'Not found'}")
    progress_logger.info(f"Found client: {klant.get_text(strip=True) if klant else 'Not found'}")
    progress_logger.info(f"Found job description: {'Yes' if functieomschrijving else 'No'}, length: {len(str(functieomschrijving)) if functieomschrijving else 0}")
    progress_logger.info(f"Found info fields: {list(aanvraag_info.keys())}")
    
    # Build markdown output
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
        progress_logger.info(f"Function description HTML length: {len(functieomschrijving_html)}")
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
    """Genereer een embedding voor de gegeven tekst via OpenAI's API met rate limit handling."""
    # Rate limit handling variables
    max_retries = 5
    retry_delay = 1  # Initial delay in seconds
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                progress_logger.info(f"Embedding API call attempt {attempt + 1}/{max_retries}")
                
            embedding_response = client_openai.embeddings.create(
                input=text,
                model=EMBEDDING_MODEL
            )
            return embedding_response.data[0].embedding
            
        except Exception as e:
            error_str = str(e)
            # Check if this is a rate limit error
            if "rate_limit" in error_str.lower() and attempt < max_retries - 1:
                # Extract wait time if available in the error message
                wait_time_ms = 1000  # Default 1 second
                
                # Try to parse the wait time from error message
                import re
                wait_match = re.search(r'try again in (\d+)ms', error_str)
                if wait_match:
                    wait_time_ms = int(wait_match.group(1))
                    # Add a buffer to the wait time
                    wait_time_ms = int(wait_time_ms * 1.2)  # 20% buffer
                
                # Calculate wait time in seconds
                wait_time = max(wait_time_ms / 1000, retry_delay)
                
                progress_logger.warning(f"⚠️ Embedding rate limit hit. Waiting {wait_time:.2f} seconds before retry...")
                import time
                time.sleep(wait_time)
                
                # Exponential backoff for next attempt
                retry_delay = retry_delay * 2
            else:
                # For non-rate limit errors or last attempt, log and break
                logger.error(f"⚠️ Error in get_embedding (attempt {attempt+1}/{max_retries}): {error_str}")
                if attempt < max_retries - 1:
                    progress_logger.warning(f"Retrying in {retry_delay} seconds...")
                    import time
                    time.sleep(retry_delay)
                    retry_delay = retry_delay * 2
                else:
                    # This was the last attempt, raise the exception
                    raise Exception(f"Failed to generate embedding after {max_retries} attempts: {error_str}")

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

    # Rate limit handling variables
    max_retries = 3
    retry_delay = 1  # Initial delay in seconds
    
    for attempt in range(max_retries):
        try:
            progress_logger.info(f"API call attempt {attempt + 1}/{max_retries}")
            
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
            error_str = str(e)
            # Check if this is a rate limit error
            if "rate_limit" in error_str.lower() and attempt < max_retries - 1:
                # Extract wait time if available in the error message
                wait_time_ms = 2000  # Default 2 seconds
                
                # Try to parse the wait time from error message
                import re
                wait_match = re.search(r'try again in (\d+)ms', error_str)
                if wait_match:
                    wait_time_ms = int(wait_match.group(1))
                    # Add a buffer to the wait time
                    wait_time_ms = int(wait_time_ms * 1.2)  # 20% buffer
                
                # Calculate wait time in seconds
                wait_time = max(wait_time_ms / 1000, retry_delay)
                
                progress_logger.warning(f"⚠️ Rate limit hit. Waiting {wait_time:.2f} seconds before retry...")
                import time
                time.sleep(wait_time)
                
                # Exponential backoff for next attempt
                retry_delay = retry_delay * 2
            else:
                # For non-rate limit errors or last attempt, log and break
                logger.error(f"⚠️ Error in evaluate_candidate (attempt {attempt+1}/{max_retries}): {error_str}")
                if attempt < max_retries - 1:
                    progress_logger.warning(f"Retrying in {retry_delay} seconds...")
                    import time
                    time.sleep(retry_delay)
                    retry_delay = retry_delay * 2
                else:
                    # This was the last attempt, break out of the loop
                    break

    # If we got here, all retries failed
    logger.error(f"⚠️ All {max_retries} attempts failed in evaluate_candidate")
    # Return fallback evaluation
    evaluation = {
        "name": name,
        "percentage": 0,
        "sterke_punten": ["Evaluatie mislukt na meerdere pogingen"],
        "zwakke_punten": ["Evaluatie mislukt na meerdere pogingen"],
        "eindoordeel": f"Evaluatie kon niet worden voltooid na {max_retries} pogingen vanwege API limieten of fouten."
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
    
    # Initialize a list to track processed vacancies for the email digest
    processed_vacancies = []

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
        verbose=True  # Enables verbose logging
    )

    # Add debug info for the crawler
    progress_logger.info(f"Setting up crawler with the following parameters:")
    progress_logger.info(f"  Source URL: {URL1_SOURCE}")
    progress_logger.info(f"  Login URL: {URL1_LOGIN_URL}")
    progress_logger.info(f"  Provider: {URL1_PROVIDER_NAME}")
    progress_logger.info(f"  User: {URL1_SPINWEB_USER}")
    progress_logger.info(f"  Pass: {'*'*len(URL1_SPINWEB_PASS) if URL1_SPINWEB_PASS else 'Not set'}")

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
            # Check for login form and debug credentials
            progress_logger.info(f"Login credentials - User: {URL1_SPINWEB_USER}, Pass: {'*'*len(URL1_SPINWEB_PASS)}")
            progress_logger.info(f"🔑 Checking login form using selector 'input[name=\"user\"]'...")
            
            if await page.is_visible("input[name='user']"):
                progress_logger.info("🔐 Login form found. Attempting to log in...")
                await page.fill("input[name='user']", URL1_SPINWEB_USER)
                await page.fill("input[name='pass']", URL1_SPINWEB_PASS)
                
                # Take screenshot before click
                try:
                    # Create screenshots directory if needed
                    import os
                    screenshots_dir = os.path.join(os.getcwd(), "screenshots")
                    os.makedirs(screenshots_dir, exist_ok=True)
                    
                    screenshot_path = os.path.join(screenshots_dir, "pre_login.png")
                    await page.screenshot(path=screenshot_path)
                    progress_logger.info(f"📸 Took screenshot of login form: {screenshot_path}")
                except Exception as ss_err:
                    progress_logger.error(f"Failed to take screenshot: {ss_err}")
                
                # Click the login button
                progress_logger.info("Clicking submit button...")
                await page.click("button[type='submit']")
                progress_logger.info("Waiting for page to load after login...")
                await page.wait_for_load_state("networkidle", timeout=30000)
                
                # Check if login was successful by looking for login form again
                if await page.is_visible("input[name='user']"):
                    progress_logger.error("⚠️ Still seeing login form after submit - login likely failed!")
                else:
                    progress_logger.info("✅ Login form no longer visible - login appears successful")
                    
                    # Navigate to the source URL after successful login
                    try:
                        progress_logger.info(f"Navigating to source URL: {URL1_SOURCE}")
                        await page.goto(URL1_SOURCE, timeout=30000)
                        await page.wait_for_load_state("networkidle", timeout=30000)
                        progress_logger.info("✅ Successfully navigated to source URL after login")
                        
                        # Take screenshot of the vacancy page
                        try:
                            import os
                            screenshots_dir = os.path.join(os.getcwd(), "screenshots")
                            os.makedirs(screenshots_dir, exist_ok=True)
                            
                            screenshot_path = os.path.join(screenshots_dir, "vacancy_page.png")
                            await page.screenshot(path=screenshot_path)
                            progress_logger.info(f"📸 Took screenshot of vacancy page: {screenshot_path}")
                            
                            # Save the HTML of the vacancy page too
                            vacancy_html = await page.content()
                            debug_dir = os.path.join(os.getcwd(), "debug")
                            os.makedirs(debug_dir, exist_ok=True)
                            
                            with open(os.path.join(debug_dir, "vacancy_page.html"), "w") as f:
                                f.write(vacancy_html)
                            progress_logger.info("✅ Saved vacancy page HTML to debug/vacancy_page.html")
                        except Exception as e:
                            progress_logger.error(f"Failed to save vacancy page details: {str(e)}")
                    except playwright.async_api.TimeoutError as e:
                        progress_logger.error(f"⚠️ Timeout navigating to source URL: {str(e)}")
                    except playwright.async_api.Error as e:
                        progress_logger.error(f"⚠️ Error navigating to source URL: {str(e)}")
                    
                # Take screenshot after login
                try:
                    # Use the same screenshots directory
                    import os
                    screenshots_dir = os.path.join(os.getcwd(), "screenshots")
                    os.makedirs(screenshots_dir, exist_ok=True)
                    
                    screenshot_path = os.path.join(screenshots_dir, "post_login.png")
                    await page.screenshot(path=screenshot_path)
                    progress_logger.info(f"📸 Took screenshot after login attempt: {screenshot_path}")
                except Exception as ss_err:
                    progress_logger.error(f"Failed to take screenshot: {ss_err}")
                    
            else:
                progress_logger.info("✅ Login form not found - already logged in or different authentication method.")
        except playwright.async_api.TimeoutError as e:
            progress_logger.error(f"⚠️ Timeout during login process: {str(e)}")
        except playwright.async_api.Error as e:
            progress_logger.error(f"⚠️ Playwright error during login: {str(e)}")

        return page

    crawler.crawler_strategy.set_hook("on_page_context_created", on_page_context_created)

    await crawler.start()

    if not URL1_SOURCE:
        progress_logger.error("Error: No source URL configured in environment variables.")
        return []

    # We're now using a different approach: 
    # Instead of directly crawling the source URL, we first login and then navigate to the source URL
    # in the on_page_context_created hook. This allows us to maintain the login session.
    # 
    # The URL1_LOGIN_URL is used for the initial navigation, and then we navigate to URL1_SOURCE
    # after successful login. So here we use the login URL for the crawler.
    progress_logger.info("Starting crawler with initial navigation to login URL...")

    # For the initial crawl, we'll just use the login URL
    # The actual crawling of the source URL happens in the hook
    result = await crawler.arun(URL1_LOGIN_URL, config=crawler_run_config)

    if not result.success:
        progress_logger.error(f"Error crawling login URL: {result.error_message}")
        await crawler.close()
        return
    
    progress_logger.info("Crawled URL: %s", result.url)
    
    # Enhanced debugging for HTML content
    html_content = result.html
    progress_logger.info(f"HTML content length: {len(html_content)}")
    
    # Check if we have a login form in the returned HTML (indicating we're not logged in)
    login_form_present = "name='user'" in html_content or "name='pass'" in html_content
    if login_form_present:
        progress_logger.error("⚠️ WARNING: Login form detected in returned HTML - login may have failed!")
        progress_logger.error("This is a critical issue that will prevent finding vacancy links!")
        progress_logger.info(f"Using credentials: User={URL1_SPINWEB_USER}, Pass={'*'*len(URL1_SPINWEB_PASS)}")
        progress_logger.info(f"Login URL: {URL1_LOGIN_URL}")
        progress_logger.info(f"Source URL: {URL1_SOURCE}")
        
        # Save the HTML for debugging
        try:
            import os
            debug_dir = os.path.join(os.getcwd(), "debug")
            os.makedirs(debug_dir, exist_ok=True)
            
            with open(os.path.join(debug_dir, "failed_login_page.html"), "w") as f:
                f.write(html_content)
            progress_logger.info("✅ Saved login page HTML to debug/failed_login_page.html")
        except Exception as e:
            progress_logger.error(f"Could not save debug HTML: {str(e)}")
    
    # Look for title to see what page we're on
    soup = BeautifulSoup(html_content, 'html.parser')
    page_title = soup.title.string if soup.title else "No title found"
    progress_logger.info(f"Page title: {page_title}")
    
    # Debug the first 500 characters of HTML to see what we're getting
    progress_logger.info(f"HTML preview: {html_content[:500]}...")
    
    # Important: We need to use the HTML from the vacancy page, not the login page
    # Check if we have debug HTML file from the vacancy page, use that instead
    import os
    import re  # For regex pattern matching
    
    debug_dir = os.path.join(os.getcwd(), "debug")
    vacancy_page_path = os.path.join(debug_dir, "vacancy_page.html")
    vacancy_html = None
    
    if os.path.exists(vacancy_page_path):
        progress_logger.info(f"Using vacancy page HTML from debug file: {vacancy_page_path}")
        try:
            with open(vacancy_page_path, "r") as f:
                vacancy_html = f.read()
                soup = BeautifulSoup(vacancy_html, 'html.parser')
                progress_logger.info(f"Loaded vacancy page HTML - length: {len(vacancy_html)}")
        except Exception as e:
            progress_logger.error(f"Error reading vacancy page HTML: {e}")
            # Continue with the original soup
    else:
        vacancy_html = html_content  # Use the HTML from the crawler result
    
    # 1. Primary Approach: Use regex to find vacancy links, exactly like the old script
    vacancy_links = set()
    if vacancy_html:
        # Look for "/aanvraag/123456" patterns in the HTML
        aanvraag_matches = re.findall(r'/aanvraag/\d+', vacancy_html)
        progress_logger.info(f"Found {len(aanvraag_matches)} matches using regex for '/aanvraag/\\d+'")
        
        for link in aanvraag_matches:
            full_url = f"https://{URL1_PROVIDER_NAME}{link}"
            vacancy_links.add(full_url)
            progress_logger.info(f"Found vacancy link via regex: {full_url}")
    
    # 2. Secondary Approach: Find links in the parsed HTML
    if not vacancy_links:
        progress_logger.info("No vacancy links found with regex. Trying HTML parsing...")
        all_links = soup.find_all('a', href=True)
        progress_logger.info(f"Total links found: {len(all_links)}")
        
        # Expand search to include different patterns
        link_patterns = ['/aanvraag/', 'interim-aanvraag', '/opdracht/', 'interim-opdracht']
        
        for link in all_links:
            href = link['href']
            # Check for any of the link patterns
            matches_pattern = any(pattern in href for pattern in link_patterns)
            
            if matches_pattern:
                # Zorg voor volledige URLs met protocol voor de crawler
                full_url = f"https://{URL1_PROVIDER_NAME}{href}" if href.startswith('/') else href
                if not full_url.startswith('http'):
                    full_url = f"https://{full_url}"
                vacancy_links.add(full_url)
                progress_logger.info(f"Found vacancy link: {full_url}")
    
    # 3. Tertiary Approach: Look for vacancy cards
    if not vacancy_links:
        progress_logger.info("No vacancy links found with standard patterns. Trying to find vacancy cards...")
        
        vacancy_cards = soup.find_all('div', class_=lambda c: c and ('card' in c.lower() or 'vacancy' in c.lower()))
        if not vacancy_cards:
            vacancy_cards = soup.find_all('div', class_=lambda c: c and ('item' in c.lower() or 'listing' in c.lower()))
        if not vacancy_cards:
            vacancy_cards = soup.select('.item, .card, .vacancy, .job-listing, .job-item')
            
        progress_logger.info(f"Found {len(vacancy_cards)} potential vacancy cards")
        
        for card in vacancy_cards:
            links = card.find_all('a', href=True)
            for link in links:
                href = link['href']
                if '?' not in href and '#' not in href and len(href) > 5:
                    full_url = f"https://{URL1_PROVIDER_NAME}{href}" if href.startswith('/') else href
                    if not full_url.startswith('http'):
                        full_url = f"https://{full_url}"
                    vacancy_links.add(full_url)
                    progress_logger.info(f"Found vacancy link from card: {full_url}")
    
    # Debug some example links
    sample_links = [link['href'] for link in all_links[:20]] if 'all_links' in locals() else []
    if sample_links:
        progress_logger.info(f"Sample of links found: {sample_links}")
    
    # Save the found links to a debug file
    try:
        debug_dir = os.path.join(os.getcwd(), "debug")
        os.makedirs(debug_dir, exist_ok=True)
        with open(os.path.join(debug_dir, "found_vacancy_links.txt"), "w") as f:
            for link in vacancy_links:
                f.write(f"{link}\n")
        progress_logger.info(f"✅ Saved found vacancy links to debug/found_vacancy_links.txt")
    except Exception as e:
        progress_logger.error(f"Could not save vacancy links to debug file: {str(e)}")
        
    progress_logger.info(f"Found {len(vacancy_links)} vacancy links")

    # Last resort: If we still don't have any vacancy links, try a more direct page scraping approach
    if not vacancy_links:
        progress_logger.info("Still no vacancy links found. Attempting direct page scrape as last resort...")
        try:
            # Create a new browser page for direct scraping
            import os
            from playwright.async_api import async_playwright
            
            progress_logger.info("Launching direct browser instance for scraping...")
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                
                # Go to login page
                progress_logger.info(f"Navigating to login page: {URL1_LOGIN_URL}")
                await page.goto(URL1_LOGIN_URL, timeout=30000)
                await page.wait_for_load_state("networkidle", timeout=30000)
                
                # Check if we need to login
                if await page.is_visible("input[name='user']"):
                    progress_logger.info("Logging in...")
                    await page.fill("input[name='user']", URL1_SPINWEB_USER)
                    await page.fill("input[name='pass']", URL1_SPINWEB_PASS)
                    await page.click("button[type='submit']")
                    await page.wait_for_load_state("networkidle", timeout=30000)
                
                # Navigate to the source URL
                progress_logger.info(f"Navigating to source URL: {URL1_SOURCE}")
                await page.goto(URL1_SOURCE, timeout=30000)
                await page.wait_for_load_state("networkidle", timeout=30000)
                
                # Take a screenshot
                screenshots_dir = os.path.join(os.getcwd(), "screenshots")
                os.makedirs(screenshots_dir, exist_ok=True)
                screenshot_path = os.path.join(screenshots_dir, "direct_scrape.png")
                await page.screenshot(path=screenshot_path)
                progress_logger.info(f"📸 Took screenshot of direct scrape: {screenshot_path}")
                
                # Get the page content
                direct_html = await page.content()
                direct_soup = BeautifulSoup(direct_html, 'html.parser')
                
                # Save for debugging
                debug_dir = os.path.join(os.getcwd(), "debug")
                os.makedirs(debug_dir, exist_ok=True)
                with open(os.path.join(debug_dir, "direct_scrape.html"), "w") as f:
                    f.write(direct_html)
                progress_logger.info("✅ Saved direct scrape HTML to debug/direct_scrape.html")
                
                # Try to find all links
                direct_links = direct_soup.find_all('a', href=True)
                progress_logger.info(f"Found {len(direct_links)} links in direct scrape")
                
                # Look for links with vacancy patterns
                for link in direct_links:
                    href = link['href']
                    if any(pattern in href.lower() for pattern in link_patterns):
                        full_url = f"https://{URL1_PROVIDER_NAME}{href}" if href.startswith('/') else href
                        if not full_url.startswith('http'):
                            full_url = f"https://{full_url}"
                        vacancy_links.add(full_url)
                        progress_logger.info(f"Found vacancy link in direct scrape: {full_url}")
                
                # Close the browser
                await browser.close()
                progress_logger.info(f"Direct scrape found {len(vacancy_links)} vacancy links")
                
        except Exception as e:
            progress_logger.error(f"Error in direct page scrape: {str(e)}")
    
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
        
        # Log some existing URLs for debugging
        sample_existing = list(existing_aanvragen_urls)[:5]
        progress_logger.info(f"Sample existing URLs: {sample_existing}")
    except Exception as e:
        progress_logger.error(f"Error retrieving existing listings: {str(e)}")
        existing_aanvragen_urls = set()
        
    # Get highest URL (newest vacancy) as a cutoff point
    highest_url = ""
    try:
        from app.db_init import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        # Get the most recent vacancy by created_at date
        cursor.execute("SELECT url FROM vacancies ORDER BY created_at DESC LIMIT 1")
        result = cursor.fetchone()
        if result and result[0]:
            # Make sure to normalize the URL in the same way as vacancy URLs are normalized
            highest_url = normalize_url(result[0])
            progress_logger.info(f"Highest URL from database: {highest_url}")
            
            # Additional debug to check format
            original_url = result[0]
            progress_logger.info(f"Original URL: {original_url}, Normalized: {highest_url}")
            
            # Add explicit type checks for debugging
            progress_logger.info(f"URL type check - original: {type(original_url)}, normalized: {type(highest_url)}")
        else:
            progress_logger.info("No highest URL found in database (may be empty)")
        cursor.close()
        conn.close()
    except Exception as e:
        progress_logger.error(f"Error retrieving newest listing: {str(e)}")
        highest_url = ""

    # Log vacancy URLs before filtering
    progress_logger.info(f"Vacancy URLs before filtering: {len(vacancy_links_db)}")
    sample_links = list(vacancy_links_db)[:5]
    progress_logger.info(f"Sample vacancy URLs: {sample_links}")
    
    # Production logic - only process vacancies that are newer than highest_url
    # Using a more detailed filtering approach for debugging
    new_listings_db = set()
    for link in vacancy_links_db:
        if link in existing_aanvragen_urls:
            # Skip existing URLs
            continue
        
        if not highest_url:
            # If no highest_url (empty DB), accept all vacancies
            new_listings_db.add(link)
            continue
            
        # Only add if link is newer (numerically higher) than highest_url
        # Parse the numeric portion from vacancy URLs if possible
        try:
            # This handles URLs like "spinweb.nl/aanvraag/123456"
            link_num = int(link.split('/')[-1]) if '/' in link else 0
            highest_num = int(highest_url.split('/')[-1]) if '/' in highest_url else 0
            
            if link_num > highest_num:
                new_listings_db.add(link)
                progress_logger.info(f"Comparing numbers: {link_num} > {highest_num} = {link_num > highest_num}")
            else:
                progress_logger.info(f"Filtering out: {link_num} <= {highest_num} = {link_num <= highest_num}")
        except (ValueError, IndexError):
            # Fallback to string comparison if we can't parse numbers
            if link > highest_url:
                new_listings_db.add(link)
                progress_logger.info(f"String comparison fallback: {link} > {highest_url}")
            else:
                progress_logger.info(f"Filtering out (string): {link} <= {highest_url}")
    
    # Sort listings for processing (ensure they're processed in order)
    new_listings_db = sorted(new_listings_db)
    
    # Log details of filtering with more debug info
    progress_logger.info(f"Vacancy URLs after filtering: {len(new_listings_db)}")
    progress_logger.info(f"Highest URL cutoff: '{highest_url}'")  # Debug the exact highest value
    
    for link in vacancy_links_db:
        if link in existing_aanvragen_urls:
            progress_logger.info(f"URL filtered (exists in DB): {link}")
        elif highest_url and link <= highest_url:
            progress_logger.info(f"URL filtered (not newer than highest): '{link}' <= '{highest_url}' = {link <= highest_url}")
        else:
            progress_logger.info(f"URL accepted for processing: '{link}' > '{highest_url}' = {not highest_url or link > highest_url}")

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
            
            # Function to parse dates into standard format
            def parse_date(value):
                """Convert a date string to the standard format or return None if invalid."""
                import datetime as dt  # Import locally to ensure availability
                
                if not value:
                    return None
                
                # Clean the input
                value = value.strip()
                
                try:
                    # Try different date formats
                    formats = [
                        '%d-%m-%Y',     # 14-03-2025
                        '%d/%m/%Y',     # 14/03/2025
                        '%Y-%m-%d',     # 2025-03-14
                        '%B %d, %Y',    # March 14, 2025
                        '%d %B %Y',     # 14 March 2025
                        '%d %b %Y'      # 14 Mar 2025
                    ]
                    
                    for fmt in formats:
                        try:
                            date_obj = dt.datetime.strptime(value, fmt)
                            # Always return in PostgreSQL-compatible format
                            formatted_date = date_obj.strftime('%Y-%m-%d')
                            logging.info(f"Successfully parsed date '{value}' to '{formatted_date}'")
                            return formatted_date
                        except ValueError:
                            continue
                    
                    # If we can't parse the date, return None instead of the raw string
                    logging.warning(f"Couldn't parse date: '{value}'")
                    return None
                except Exception as e:
                    logging.error(f"Error parsing date: {value} - {str(e)}")
                    return None
            
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
                        raw_date = line.replace("- **Geplaatst:**", "").strip()
                        data["Geplaatst"] = parse_date(raw_date)
                    elif line.startswith("- **Sluitingsdatum:**"):
                        raw_date = line.replace("- **Sluitingsdatum:**", "").strip()
                        data["Sluiting"] = parse_date(raw_date)
                    elif line.startswith("- **Sluiting:**"):
                        raw_date = line.replace("- **Sluiting:**", "").strip()
                        data["Sluiting"] = parse_date(raw_date)
                
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
                        # Log the date values for debugging
                        progress_logger.info(f"Date values - Geplaatst: {vacancy_data.get('Geplaatst')}, Sluiting: {vacancy_data.get('Sluiting')}")
                        
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
                                vacancy_data.get("Geplaatst"),  # Date may be None if parsing failed
                                vacancy_data.get("Sluiting"),  # Date may be None if parsing failed
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
                            INSERT INTO vacancies (url, functie, klant, functieomschrijving, status, geplaatst, sluiting, created_at, updated_at) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                            RETURNING id
                            """,
                            (
                                db_url,
                                vacancy_data.get("Functie", ""),
                                vacancy_data.get("Klant", ""),
                                vacancy_data.get("Functieomschrijving", ""),
                                vacancy_data.get("Status", "Nieuw"),
                                vacancy_data.get("Geplaatst"),
                                vacancy_data.get("Sluiting")
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
                        
                        # Add to processed vacancies for email digest
                        processed_vacancies.append({
                            'url': db_url,
                            'Functie': vacancy_data.get('Functie', 'Onbekend'),
                            'Klant': vacancy_data.get('Klant', 'Onbekend'),
                            'Status': match_results.get('Status', 'Open'),
                            'Top_Match': match_results.get('Top_Match', 0),
                            'Checked_resumes': match_results.get('Checked_resumes', '')
                        })
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
                        
                        # Add to processed vacancies for email digest
                        processed_vacancies.append({
                            'url': db_url,
                            'Functie': vacancy_data.get('Functie', 'Onbekend'),
                            'Klant': vacancy_data.get('Klant', 'Onbekend'),
                            'Status': 'AI afgewezen',
                            'Top_Match': 0,
                            'Checked_resumes': ''
                        })
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
    
    # Calculate average tokens per evaluation
    avg_tokens = 0
    if total_token_usage['total_evaluations'] > 0:
        avg_tokens = total_token_usage['total_tokens'] / total_token_usage['total_evaluations']
        progress_logger.info(f"Gemiddeld tokens per evaluatie: {avg_tokens:.2f}")
    
    # Prepare to send email digest if enabled
    try:
        if processed_vacancies:
            # Get processed vacancies from database for email digest
            from app.db_init import get_connection
            conn = get_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Fetch the recently processed vacancies
            processed_urls = [data.get('url') for data in processed_vacancies if data.get('url')]
            if processed_urls:
                placeholders = ','.join(['%s'] * len(processed_urls))
                cursor.execute(
                    f"""
                    SELECT id, functie, klant, status, top_match, checked_resumes, url
                    FROM vacancies 
                    WHERE url IN ({placeholders})
                    ORDER BY updated_at DESC
                    """,
                    processed_urls
                )
            else:
                # Fallback: If no processed_vacancies were tracked, get recently updated ones
                cursor.execute(
                    """
                    SELECT id, functie, klant, status, top_match, checked_resumes, url
                    FROM vacancies 
                    WHERE updated_at > NOW() - INTERVAL '1 hour'
                    ORDER BY updated_at DESC
                    """
                )
                
            # Convert to list of dictionaries for email service
            email_vacancy_data = []
            for row in cursor.fetchall():
                email_vacancy_data.append(dict(row))
            
            # Prepare processing stats for email
            processing_stats = {
                'total_time': f"{total_token_usage.get('total_processing_time', 0):.2f} seconds",
                'token_usage': f"{total_token_usage.get('total_tokens', 0)} tokens",
                'avg_tokens': f"{avg_tokens:.2f} tokens/evaluation" if avg_tokens > 0 else "N/A"
            }
            
            # Send email digest if we have any data
            if email_vacancy_data:
                email_sent = email_service.send_digest(email_vacancy_data, processing_stats)
                if email_sent:
                    progress_logger.info("✅ Email digest sent successfully")
                else:
                    progress_logger.info("ℹ️ Email digest not sent (service disabled or no recipients configured)")
            else:
                progress_logger.info("ℹ️ No vacancies processed, skipping email digest")
            
            cursor.close()
            conn.close()
        
    except Exception as e:
        progress_logger.error(f"❌ Failed to send email digest: {str(e)}")
        import traceback
        traceback.print_exc()

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
