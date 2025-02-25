#!/usr/bin/env python3
"""
Gecombineerd Vacature & Resume Matching Proces

Dit script voert zowel het scrapen van Spinweb vacatures als het matchen met CV's uit in één geïntegreerd proces:
1. Scrapen van nieuwe vacatures van Spinweb.nl
2. Verwerken en opslaan in NocoDB
3. Matchen van CV's met nieuwe vacatures
4. Bijwerken van match resultaten in NocoDB

Author: Daniel Tromp
Email: drpgmtromp@gmail.com
Version: 1.0.0
Created: 2025-02-25
License: MIT
Repository: https://github.com/DanielTromp/ResumeAI
"""

# Standard library imports
import os
import json
import asyncio
import logging
import logging.handlers
import requests
from collections import defaultdict

# Third-party imports
import html2text
import supabase
import tiktoken
from openai import OpenAI
import playwright.async_api
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

# Project specific imports
from config import *
from components.nocodb_client import NocoDBClient

# Configureer logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client_openai = OpenAI(api_key=OPENAI_API_KEY)

# Initialize token calculator
enc = tiktoken.encoding_for_model("gpt-4o-mini")

# Initialize Supabase client
supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize NocoDB client
nocodb = NocoDBClient()

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
        'NOCODB_TOKEN': NOCODB_TOKEN,
        'NOCODB_PROJECT': NOCODB_PROJECT,
        'NOCODB_TABLE': NOCODB_TABLE,
        'URL1_SPINWEB_USER': URL1_SPINWEB_USER,
        'URL1_SPINWEB_PASS': URL1_SPINWEB_PASS,
        'URL1_LOGIN_URL': URL1_LOGIN_URL,
        'URL1_PROVIDER_NAME': URL1_PROVIDER_NAME,
        'URL1_SOURCE': URL1_SOURCE,
        'OPENAI_API_KEY': OPENAI_API_KEY,
        'SUPABASE_URL': SUPABASE_URL,
        'SUPABASE_KEY': SUPABASE_KEY
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
    """Evalueer een kandidaat CV tegen een vacature tekst met GPT-4o-mini."""
    prompt = f"""
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

    # Bereken tokens
    input_tokens = len(enc.encode(prompt))
    
    try:
        response = client_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Je bent een AI die sollicitanten evalueert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=800,
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
    logger.info(f"\n📊 Start evaluatie van {len(matches)} kandidaten voor vacature {vacancy_id}")
    
    all_evaluations = []
    token_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "evaluations_count": 0}
    
    for name, chunks in matches.items():
        logger.info(f"  👤 Evalueren van kandidaat: {name}")
        cv_text = " ".join(chunks)
        evaluation, tokens = evaluate_candidate(name, cv_text, vacancy_text)
        all_evaluations.append(evaluation)
        token_usage["input_tokens"] += tokens["input_tokens"]
        token_usage["output_tokens"] += tokens["output_tokens"]
        token_usage["total_tokens"] += tokens["total_tokens"]
        token_usage["evaluations_count"] += 1
        logger.info(f"    ✓ Match percentage: {evaluation['percentage']}%")
    
    sorted_evaluations = sorted(all_evaluations, key=lambda x: x["percentage"], reverse=True)
    top_evaluations = sorted_evaluations[:5]
    best_match = top_evaluations[0] if top_evaluations else None
    
    if best_match:
        new_status = "Open" if best_match["percentage"] >= 60 else "AI afgewezen"
        # Maak een payload met alle relevante kolommen voor NocoDB
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
    logger.info("🔍 Start gecombineerd vacature ophalen & matching process")
    
    # Cleanup gesloten listings
    nocodb.cleanup_closed_listings()

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
        logger.info("[HOOK] Setting up page & context.")
        try:
            await page.goto(URL1_LOGIN_URL, timeout=10000)
        except playwright.async_api.TimeoutError as e:
            logger.error("Timeout loading login page: %s", e)
            return page
        except playwright.async_api.Error as e:
            logger.error("Playwright error loading login page: %s", e)
            return page

        try:
            if await page.is_visible("input[name='user']"):
                logger.info("Logging in...")
                await page.fill("input[name='user']", URL1_SPINWEB_USER)
                await page.fill("input[name='pass']", URL1_SPINWEB_PASS)
                await page.click("button[type='submit']")
                await page.wait_for_load_state("networkidle", timeout=30000)
            else:
                logger.info("Already logged in, skipping login step.")
        except playwright.async_api.TimeoutError as e:
            logger.error("Timeout during login process: %s", e)
        except playwright.async_api.Error as e:
            logger.error("Playwright error during login: %s", e)

        return page

    crawler.crawler_strategy.set_hook("on_page_context_created", on_page_context_created)

    await crawler.start()

    if not URL1_SOURCE:
        logger.error("Error: No source URL configured in environment variables.")
        return []

    result = await crawler.arun(URL1_SOURCE, config=crawler_run_config)
    
    if not result.success:
        logger.error("Error crawling source URL: %s", result.error_message)
        await crawler.close()
        return
    
    logger.info("Crawled URL: %s", result.url)
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
    
    logger.info(f"Found {len(vacancy_links)} vacancy links")
    
    # URL normalisatie voor database en crawler
    # Voor database: zonder protocol (spinweb.nl/aanvraag/123)
    # Voor crawler: met protocol (https://spinweb.nl/aanvraag/123)
    vacancy_links_db = {nocodb.normalize_url(link) for link in vacancy_links}
    vacancy_links_crawler = {link for link in vacancy_links}  # Behoud originele URLs met protocol
    
    # Maak een mapping van database URLs naar crawler URLs
    vacancy_links_map = {}
    for link in vacancy_links:
        db_url = nocodb.normalize_url(link)
        vacancy_links_map[db_url] = link  # Gebruik originele URL met protocol voor crawler
    
    # Normaliseer bestaande listings uit NocoDB
    existing_aanvragen_urls = {nocodb.normalize_url(url) for url in nocodb.get_existing_listings()}
    lowest_url = nocodb.normalize_url(nocodb.get_lowest_listing_url())

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
            logger.warning(f"URL {db_url} niet gevonden in mapping, fallback gebruikt: {crawler_url}")

    logger.info(f"Found {len(new_listings_db)} new vacancies to process")
    
    # Verwerk elke nieuwe vacature: ophalen, matchen, en dan pas opslaan
    excluded_clients = EXCLUDED_CLIENTS
    logger.info(f"ℹ️ Uitgesloten klanten geladen: {len(excluded_clients)}")
    total_token_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "total_evaluations": 0}
    
    for i, db_url in enumerate(new_listings_db):
        crawler_url = new_listings_crawler[i]
        logger.info(f"\n=== Verwerken vacature {i+1}/{len(new_listings_db)}: {db_url} ===")
        
        # Stap 1: Vacature details ophalen
        try:
            result = await crawler.arun(crawler_url, config=crawler_run_config)
            if not result.success:
                logger.error(f"Error crawling {crawler_url}: {result.error_message}")
                continue
                
            logger.info(f"Succesvol gecrawled: {crawler_url}")
            markdown_data = extract_data_from_html(result.html, db_url)
            vacancy_data = nocodb._parse_markdown_data(markdown_data, db_url)
            
            # Check of de klant op de uitsluitlijst staat
            client_name = vacancy_data.get("Klant", "").strip()
            if client_name in excluded_clients:
                logger.info(f"⏭️ Klant '{client_name}' staat op de uitsluitlijst; markeer als AI afgewezen.")
                vacancy_data["Status"] = "AI afgewezen"
                vacancy_data["Checked_resumes"] = ""
                vacancy_data["Top_Match"] = 0
                vacancy_data["Match Toelichting"] = "Klant staat op de uitsluitlijst"
                nocodb.update_record(vacancy_data, db_url)
                continue
            
            # Stap 2: CV matching uitvoeren
            vacancy_text = vacancy_data.get("Functieomschrijving", "")
            if not vacancy_text:
                logger.warning(f"⚠️ Geen functiebeschrijving gevonden voor {db_url}, overslaan.")
                vacancy_data["Status"] = "Nieuw - Geen beschrijving"
                nocodb.update_record(vacancy_data, db_url)
                continue
            
            # Genereer embedding en zoek matches
            logger.info(f"Genereren embedding en zoeken naar CV matches...")
            vacancy_embedding = get_embedding(vacancy_text)
            try:
                query = supabase_client.rpc(
                    RESUME_RPC_FUNCTION_NAME,
                    {
                        "query_embedding": vacancy_embedding,
                        "match_threshold": MATCH_THRESHOLD,
                        "match_count": MATCH_COUNT
                    }
                ).execute()
                
                if not query.data:
                    logger.warning(f"⚠️ Geen CV matches gevonden")
                    vacancy_data["Status"] = "AI afgewezen"
                    vacancy_data["Checked_resumes"] = ""
                    vacancy_data["Top_Match"] = 0
                    vacancy_data["Match Toelichting"] = "Geen matches gevonden"
                    nocodb.update_record(vacancy_data, db_url)
                    continue
                
                # Verwerk matches
                matches = defaultdict(list)
                for item in query.data:
                    matches[item["name"]].append(item["cv_chunk"])
                
                logger.info(f"📝 {len(matches)} kandidaten gevonden voor evaluatie")
                match_results, vacancy_tokens = process_vacancy(0, vacancy_text, matches)  # 0 is dummy ID
                
                total_token_usage["input_tokens"] += vacancy_tokens["input_tokens"]
                total_token_usage["output_tokens"] += vacancy_tokens["output_tokens"]
                total_token_usage["total_tokens"] += vacancy_tokens["total_tokens"]
                total_token_usage["total_evaluations"] += vacancy_tokens["evaluations_count"]
                
                if match_results:
                    # Update de vacature data met match resultaten
                    vacancy_data.update(match_results)
                    logger.info(f"Match resultaten toegevoegd aan vacature data")
                else:
                    logger.warning(f"⚠️ Geen match resultaten gegenereerd")
                    vacancy_data["Status"] = "AI afgewezen"
                    vacancy_data["Checked_resumes"] = ""
                    vacancy_data["Top_Match"] = 0
                    vacancy_data["Match Toelichting"] = "Geen resultaten gegenereerd"
            
            except Exception as e:
                logger.error(f"⚠️ Fout bij CV matching: {str(e)}", exc_info=True)
                vacancy_data["Status"] = "Error"
                vacancy_data["Checked_resumes"] = ""
                vacancy_data["Top_Match"] = 0
                vacancy_data["Match Toelichting"] = f"Fout tijdens matching: {str(e)}"
            
            # Stap 3: Alle data in één keer opslaan
            logger.info(f"Opslaan van complete vacature data in NocoDB...")
            success = nocodb.update_record(vacancy_data, db_url)
            if success:
                logger.info(f"✅ Vacature {db_url} succesvol opgeslagen")
            else:
                logger.error(f"❌ Fout bij opslaan vacature {db_url}")
                
        except Exception as e:
            logger.error(f"⚠️ Onverwachte fout bij verwerken vacature {db_url}: {str(e)}", exc_info=True)

    await crawler.close()
    
    # Eindrapport
    logger.info("\n🚀 Alle vacatures verwerkt!")
    logger.info("\n📈 Eindrapport token gebruik:")
    logger.info(f"Totale input tokens: {total_token_usage['input_tokens']}")
    logger.info(f"Totale output tokens: {total_token_usage['output_tokens']}")
    logger.info(f"Totaal aantal tokens: {total_token_usage['total_tokens']}")
    logger.info(f"Totaal aantal evaluaties: {total_token_usage['total_evaluations']}")
    if total_token_usage['total_evaluations'] > 0:
        avg = total_token_usage['total_tokens'] / total_token_usage['total_evaluations']
        logger.info(f"Gemiddeld tokens per evaluatie: {avg:.2f}")

async def main():
    """Main function voor het volledige proces."""
    try:
        # Check environment variables
        check_environment_variables()
        
        # Voer het gecombineerde proces uit in één stap
        logger.info("🚀 Start gecombineerd vacature & CV match proces")
        await spider_vacatures()
        
        logger.info("✅ Volledig proces succesvol afgerond!")
    except Exception as e:
        logger.error(f"❌ Fout in het gecombineerde proces: {str(e)}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main()) 