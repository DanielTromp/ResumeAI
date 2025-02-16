#!/usr/bin/env python3
"""
Spinweb Vacancy Scraper

Dit script crawlt de Spinweb website om nieuwe vacatures te vinden en deze naar Airtable te uploaden.
Het voert de volgende taken uit:
1. Inloggen op Spinweb
2. Ophalen van nieuwe vacature listings
3. Vergelijken met bestaande listings in Airtable
4. Extractie van vacature details
5. Uploaden van nieuwe vacatures naar Airtable

Author: Daniel Tromp
Email: drpgmtromp@gmail.com
Version: 1.0.0
Created: 2025-02-11
Updated: 2025-02-11
License: MIT
Repository: https://github.com/DanielTromp/ResumeAI
"""

# Standaard bibliotheek imports
import asyncio
import datetime
import logging
import logging.handlers
import os
import re

# Third-party imports
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from dotenv import load_dotenv
import openai
from playwright.async_api import Page, BrowserContext
import playwright.async_api
from pyairtable import Api
import requests
import html2text

# Load environment variables
load_dotenv()
USER = os.getenv("SPINWEB_USER")
PASSWORD = os.getenv("SPINWEB_PASS")
LOGIN_URL = os.getenv("SPINWEB_LOGIN")
SOURCE_URL = os.getenv("SOURCE_URL")
PROVIDER_NAME = os.getenv("PROVIDER_NAME", "provider")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME_AANVRAGEN = os.getenv("AIRTABLE_TABLE_NAME_AANVRAGEN")

def convert_html_to_markdown(html_text: str) -> str:
    """Zet HTML om naar Markdown met behoud van de opmaak."""
    converter = html2text.HTML2Text()
    converter.ignore_links = False      # Zorgt dat links worden omgezet
    converter.ignore_images = False     # Converteer ook afbeeldingen, indien gewenst
    converter.body_width = 0              # Voorkom automatische lijnbrekingen
    markdown_text = converter.handle(html_text)
    return markdown_text.strip()

# Configureer logging
def setup_logging() -> logging.Logger:
    """Setup logging met file rotation."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Verwijder bestaande handlers om dubbele logging te voorkomen
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler met rotation
    log_file = 'spinweb_scraper.log'
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=1024 * 1024,  # 1 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger

class AirtableClient:
    """Centrale class voor Airtable interacties."""
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        try:
            self.api = Api(AIRTABLE_API_KEY)
            self.processed_table = self.api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME_AANVRAGEN)
        except requests.RequestException as e:
            self.logger.error("Network error initializing Airtable API: %s", e)
            raise
        except ValueError as e:
            self.logger.error("Invalid API key or table configuration: %s", e)
            raise
        except (KeyError, TypeError) as e:
            self.logger.error("Invalid configuration parameters: %s", e)
            raise
        except AttributeError as e:
            self.logger.error("Missing required Airtable configuration: %s", e)
            raise

    def sanitize_url(self, url: str) -> str:
        """Sanitize een URL voor gebruik in Airtable formules."""
        # Escape single quotes voor gebruik in Airtable formule
        return url.replace("'", "\\'")

    def get_existing_listings(self) -> set:
        """Haalt bestaande listings op uit Airtable."""
        try:
            records = self.processed_table.all()
            listings = {record['fields']['Listing']
                       for record in records
                       if 'Listing' in record['fields']}
            self.logger.info("Found %d existing listings", len(listings))
            return listings
        except requests.RequestException as e:
            self.logger.error("Network error getting listings from Airtable: %s", e)
            return set()
        except KeyError as e:
            self.logger.error("Data structure error in Airtable response: %s", e)
            return set()
        except (TypeError, ValueError) as e:
            self.logger.error("Data format error in Airtable response: %s", e)
            return set()
        except AttributeError as e:
            self.logger.error("Missing required Airtable configuration: %s", e)
            return set()

    def get_table_schema(self) -> None:
        """Debug functie om tabel structuur te printen."""
        try:
            record = self.processed_table.first()
            if record:
                self.logger.info("Available fields: %s", list(record['fields'].keys()))
            else:
                self.logger.info("No records found in table")
        except requests.RequestException as e:
            self.logger.error("Network error getting table schema: %s", e)
        except KeyError as e:
            self.logger.error("Invalid table structure: %s", e)
        except (TypeError, ValueError) as e:
            self.logger.error("Data type error in table schema: %s", e)
        except AttributeError as e:
            self.logger.error("Missing required table configuration: %s", e)

    def add_processed_listing(self, listing_url: str) -> None:
        """Voegt een verwerkte listing URL toe aan Airtable."""
        try:
            self.processed_table.create({"Listing": listing_url})
            self.logger.info("Added %s to processed listings", listing_url)
        except requests.RequestException as e:
            self.logger.error("Network error adding listing: %s", e)
        except ValueError as e:
            self.logger.error("Invalid data format: %s", e)
        except TypeError as e:
            self.logger.error("Invalid data type: %s", e)
        except AttributeError as e:
            self.logger.error("Missing required table configuration: %s", e)

    def add_or_update_listing(self, listing_url: str) -> None:
        """Voegt een nieuwe listing toe of werkt bestaande bij in Airtable."""
        try:
            safe_url = self.sanitize_url(listing_url)
            existing_records = self.processed_table.all(
                formula=f"FIND('{safe_url}', {{Listing}})"
            )

            if existing_records:
                record_id = existing_records[0]['id']
                self.processed_table.update(record_id, {'Listing': listing_url})
                self.logger.info("Successfully updated listing %s in Airtable", listing_url)
            else:
                self.processed_table.create({'Listing': listing_url})
                self.logger.info("Successfully added listing %s to Airtable", listing_url)
        except requests.RequestException as e:
            self.logger.error("Network error updating Airtable: %s", e)
        except ValueError as e:
            self.logger.error("Invalid data format: %s", e)
        except KeyError as e:
            self.logger.error("Missing required field: %s", e)
        except TypeError as e:
            self.logger.error("Invalid data type: %s", e)
        except AttributeError as e:
            self.logger.error("Missing required table configuration: %s", e)

    def parse_date(self, value: str, key: str) -> str:
        """Parse een datum string naar het juiste formaat."""
        try:
            date_obj = datetime.datetime.strptime(value, '%d-%m-%Y')
            return date_obj.strftime('%Y-%m-%d')
        except ValueError as e:
            self.logger.error("Fout bij parsen van datum '%s': %s", key, e)
            return value

    def add_to_airtable(self, markdown_data: str, listing_url: str) -> None:
        """Voegt een nieuwe aanvraag toe aan de Aanvragen tabel."""
        logger = logging.getLogger(__name__)
        api = Api(AIRTABLE_API_KEY)
        table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME_AANVRAGEN)

        lines = markdown_data.split('\n')
        data = {
            'URL': listing_url,
            'Status': 'Nieuw'
        }

        # Extract data from markdown
        for line in lines:
            if line.startswith('- **'):
                key_value = line.replace('- **', '').split(':** ')
                if len(key_value) == 2:
                    key, value = key_value
                    if key == 'Functie':
                        data['Functie'] = value
                    elif key == 'Klant':
                        data['Klant'] = value
                    elif key == 'Branche':
                        data['Branche'] = value
                    elif key == 'Regio':
                        data['Regio'] = value
                    elif key == 'Uren':
                        value = value.replace("onbekend", "").strip()
                        data['Uren'] = value
                    elif key == 'Tarief':
                        data['Tarief'] = value
                    elif key == 'Geplaatst':
                        try:
                            date_obj = datetime.datetime.strptime(value, '%d-%m-%Y')
                            data['Geplaatst'] = date_obj.strftime('%Y-%m-%d')
                        except ValueError as e:
                            logger.error("Error parsing 'Geplaatst' date: %s", e)
                            data['Geplaatst'] = value
                    elif key == 'Sluiting':
                        try:
                            date_obj = datetime.datetime.strptime(value, '%d-%m-%Y')
                            data['Sluiting'] = date_obj.strftime('%Y-%m-%d')
                        except ValueError as e:
                            logger.error("Error parsing 'Sluiting' date: %s", e)
                            data['Sluiting'] = value

        sections = markdown_data.split('## Functieomschrijving')
        if len(sections) > 1:
            functieomschrijving = sections[-1].strip()
            data['Functieomschrijving'] = functieomschrijving

        try:
            # Zoek bestaande record met dezelfde URL
            safe_url = self.sanitize_url(listing_url)
            existing_records = table.all(
                formula="FIND('%s', {URL})" % safe_url
            )

            if existing_records:
                record_id = existing_records[0]['id']
                table.update(record_id, data)
                self.logger.info("Successfully updated aanvraag %s in Airtable", listing_url)
            else:
                table.create(data)
                self.logger.info("Successfully added aanvraag %s to Airtable", listing_url)
        except requests.RequestException as e:
            self.logger.error("Network error adding aanvraag to Airtable: %s", e)
        except ValueError as e:
            self.logger.error("Invalid data for aanvraag: %s", e)
        except KeyError as e:
            self.logger.error("Missing required field: %s", e)
        except TypeError as e:
            self.logger.error("Invalid data type: %s", e)
        except AttributeError as e:
            self.logger.error("Missing required table configuration: %s", e)

def extract_data_from_html(html, url):
    """Extracts structured data from HTML and converts it to Markdown."""
    logger = logging.getLogger(__name__)
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
        # Haal de gehele HTML op van de functieomschrijving
        functieomschrijving_html = str(functieomschrijving)
    else:
        functieomschrijving_html = "<p>Geen omschrijving beschikbaar.</p>"

    # Converteer de HTML naar Markdown
    markdown_functieomschrijving = convert_html_to_markdown(functieomschrijving_html)

    markdown_output += "\n## Functieomschrijving\n" + markdown_functieomschrijving + "\n\n"

    return markdown_output

def check_environment_variables():
    """Controleert of alle benodigde environment variabelen zijn ingesteld."""
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "AIRTABLE_API_KEY",
        "AIRTABLE_BASE_ID",
        "AIRTABLE_TABLE_NAME_AANVRAGEN",
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(
            f"Missende environment variabelen: {', '.join(missing_vars)}"
        )

async def cleanup_closed_listings():
    """
    Verwijdert alle listings met status 'Closed' uit de Airtable.
    
    Returns:
        int: Aantal verwijderde listings
    """
    logger = logging.getLogger(__name__)
    logger.info("Start opschonen van gesloten listings")
    
    try:
        # Initialiseer Airtable client
        api = Api(AIRTABLE_API_KEY)
        table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME_AANVRAGEN)
        
        # Haal alle records op met status 'Closed'
        closed_records = table.all(formula="Status='Closed'")
        
        if not closed_records:
            logger.info("Geen gesloten listings gevonden om op te schonen")
            return 0
            
        # Verwijder de gesloten records
        record_ids = [record['id'] for record in closed_records]
        table.batch_delete(record_ids)
        
        logger.info(f"Succesvol {len(record_ids)} gesloten listings verwijderd")
        return len(record_ids)
        
    except Exception as e:
        logger.error(f"Fout bij opschonen van gesloten listings: {str(e)}")
        raise

def get_lowest_listing_url() -> str:
    """
    Haalt de URL op met de laagste waarde uit de Aanvragen tabel.
    
    Returns:
        str: De URL met de laagste waarde, of een default URL als er geen entries zijn
    """
    logger = logging.getLogger(__name__)
    try:
        api = Api(AIRTABLE_API_KEY)
        table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME_AANVRAGEN)
        
        # Haal alle records op en sorteer ze op URL
        records = table.all(sort=['URL'])
        
        if not records:
            logger.warning("Geen entries gevonden in Aanvragen tabel")
            return "https://spinweb.nl/vacature/864984"  # Fallback URL
            
        # Pak de eerste URL (laagste waarde)
        lowest_url = records[0]['fields'].get('URL', '')
        
        if not lowest_url:
            logger.warning("Geen URL gevonden in eerste record")
            return "https://spinweb.nl/vacature/864984"  # Fallback URL
            
        logger.info(f"Laagste URL gevonden: {lowest_url}")
        return lowest_url
        
    except Exception as e:
        logger.error(f"Fout bij ophalen laagste URL: {str(e)}")
        return "https://spinweb.nl/vacature/864984"  # Fallback URL

def get_existing_urls_from_aanvragen() -> set:
    """
    Haalt alle bestaande URLs op uit de Aanvragen tabel.
    
    Returns:
        set: Set van alle URLs in de Aanvragen tabel
    """
    logger = logging.getLogger(__name__)
    try:
        api = Api(AIRTABLE_API_KEY)
        table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME_AANVRAGEN)
        
        # Haal alle records op
        records = table.all()
        
        # Verzamel alle URLs in een set
        urls = {record['fields'].get('URL', '') for record in records if 'URL' in record['fields']}
        
        logger.info(f"Gevonden {len(urls)} bestaande URLs in Aanvragen tabel")
        return urls
        
    except Exception as e:
        logger.error(f"Fout bij ophalen bestaande URLs uit Aanvragen: {str(e)}")
        return set()

async def main():
    """
    Hoofdfunctie voor de Spinweb vacancy scraper.
    
    Deze functie voert de volgende stappen uit:
    1. Setup logging met file rotation
    2. Controleert environment variabelen
    3. Verwijdert gesloten listings
    4. Configureert de crawler
    5. Voert de crawler uit op de Spinweb website
    6. Verwerkt de gevonden vacatures
    """
    logger = setup_logging()
    logger.info("Starting vacancy scraper")
    
    check_environment_variables()
    
    # Voeg cleanup toe als eerste stap
    try:
        removed_count = await cleanup_closed_listings()
        logger.info(f"Opschonen voltooid: {removed_count} gesloten listings verwijderd")
    except Exception as e:
        logger.error(f"Fout bij opschonen van listings: {str(e)}")
        return
    
    # Initialiseer Airtable client
    airtable = AirtableClient()
    airtable.get_table_schema()

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
    async def on_page_context_created(page: Page, browser_context: BrowserContext = None, **kwargs):  # pylint: disable=unused-argument
        """Hook voor het instellen van de pagina en context na creatie.
        
        Args:
            page: De Playwright Page instance
            browser_context: Optionele BrowserContext parameter
            **kwargs: Extra keyword arguments die door crawl4ai worden meegegeven
        
        Returns:
            De geconfigureerde Page instance
        """
        logger = logging.getLogger(__name__)
        logger.info("[HOOK] Setting up page & context.")
        try:
            await page.goto(LOGIN_URL, timeout=10000)
        except playwright.async_api.TimeoutError as e:
            logger.error("Timeout loading login page: %s", e)
            return page
        except playwright.async_api.Error as e:
            logger.error("Playwright error loading login page: %s", e)
            return page

        try:
            if await page.is_visible("input[name='user']"):
                logger.info("Logging in...")
                await page.fill("input[name='user']", USER)
                await page.fill("input[name='pass']", PASSWORD)
                await page.click("button[type='submit']")
                await page.wait_for_load_state("networkidle", timeout=10000)
            else:
                logger.info("Already logged in, skipping login step.")
        except playwright.async_api.TimeoutError as e:
            logger.error("Timeout during login process: %s", e)
        except playwright.async_api.Error as e:
            logger.error("Playwright error during login: %s", e)

        return page

    crawler.crawler_strategy.set_hook("on_page_context_created", on_page_context_created)

    await crawler.start()

    if not SOURCE_URL:
        logger.error("Error: No source URL configured in environment variables.")
        return

    result = await crawler.arun(SOURCE_URL, config=crawler_run_config)
    if result.success:
        logger.info("Crawled URL: %s", result.url)
        vacancy_links = set(f"https://{PROVIDER_NAME}" + link for link in re.findall(r'/aanvraag/\d+', result.html))

        existing_aanvragen_urls = get_existing_urls_from_aanvragen()
        lowest_url = get_lowest_listing_url()

        # Vereenvoudigde filtering zonder existing_listings check
        new_listings = {link for link in vacancy_links
                       if link not in existing_aanvragen_urls
                       and link > lowest_url}
        new_listings = sorted(new_listings)

        logger.info(f"Gevonden {len(new_listings)} nieuwe vacatures om te verwerken")
        for listing_url in new_listings.copy():
            result = await crawler.arun(listing_url, config=crawler_run_config)
            if result.success:
                logger.info("Crawled URL: %s", listing_url)
                markdown_data = extract_data_from_html(result.html, listing_url)

                try:
                    # Eerst proberen de aanvraag toe te voegen
                    airtable.add_to_airtable(markdown_data, listing_url)
                except requests.RequestException as e:
                    logger.error("Netwerk fout bij toevoegen aan Airtable: %s - %s",
                               listing_url, str(e))
                    continue
                except ValueError as e:
                    logger.error("Ongeldige data voor Airtable: %s - %s",
                               listing_url, str(e))
                    continue
                except KeyError as e:
                    logger.error("Ontbrekend verplicht veld: %s - %s",
                               listing_url, str(e))
                    continue
                except (TypeError, AttributeError) as e:
                    logger.error("Data structuur fout: %s - %s",
                               listing_url, str(e))
                    continue

                new_listings.remove(listing_url)
            else:
                logger.error("Error crawling %s: %s", listing_url, result.error_message)
    else:
        logger.error("Error crawling source URL: %s", result.error_message)

    await crawler.close()

if __name__ == "__main__":
    asyncio.run(main())

# End of script
