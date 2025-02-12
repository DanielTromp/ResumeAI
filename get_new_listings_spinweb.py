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
import sys
import json

# Third-party imports
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from dotenv import load_dotenv
import openai
from playwright.async_api import Page, BrowserContext
import playwright.async_api
from pyairtable import Api
import requests

# Load environment variables
load_dotenv()
USER = os.getenv("SPINWEB_USER")
PASSWORD = os.getenv("SPINWEB_PASS")
LOGIN_URL = os.getenv("SPINWEB_LOGIN")
SOURCE_URL = os.getenv("SOURCE_URL")
PROVIDER_NAME = os.getenv("PROVIDER_NAME", "provider")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME_PROCESSED = os.getenv("AIRTABLE_TABLE_NAME_PROCESSED")
AIRTABLE_TABLE_NAME_LISTINGS = os.getenv("AIRTABLE_TABLE_NAME_LISTINGS")

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
            self.listings_table = self.api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME_LISTINGS)
            self.processed_table = self.api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME_PROCESSED)
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
            records = self.listings_table.all()
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
            record = self.listings_table.first()
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
            self.listings_table.create({"Listing": listing_url})
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
            existing_records = self.listings_table.all(
                formula=f"FIND('{safe_url}', {{Listing}})"
            )

            if existing_records:
                record_id = existing_records[0]['id']
                self.listings_table.update(record_id, {'Listing': listing_url})
                self.logger.info("Successfully updated listing %s in Airtable", listing_url)
            else:
                self.listings_table.create({'Listing': listing_url})
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
        table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME_PROCESSED)

        lines = markdown_data.split('\n')
        data = {
            'URL': listing_url,
            'Status': 'New'
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

def correct_markdown_with_llm(text: str) -> tuple[str, dict]:
    """Corrigeert de markdown-opmaak met behulp van het OpenAI API."""
    logger = logging.getLogger(__name__)
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content":
                    "Je taak is om markdown-opmaak te corrigeren."
                    "Behoud de inhoud exact, verbeter alleen de opmaak."},
                {"role": "user", "content": text}
            ],
            temperature=0.0,
            max_tokens=4000,
            timeout=30
        )

        usage = {
            'input_tokens': response.usage.prompt_tokens,
            'output_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens
        }

        return response.choices[0].message.content.strip(), usage
    except openai.RateLimitError as e:
        logger.error("OpenAI Rate Limit bereikt: %s", e)
        return text, {}
    except openai.APITimeoutError as e:
        logger.error("OpenAI Timeout: %s", e)
        return text, {}
    except openai.APIConnectionError as e:
        logger.error("OpenAI Connectie probleem: %s", e)
        return text, {}
    except openai.APIError as e:
        logger.error("OpenAI API Error: %s", e)
        return text, {}
    except (ValueError, TypeError) as e:
        logger.error("Ongeldige input parameters: %s", e)
        return text, {}
    except AttributeError as e:
        logger.error("Ontbrekende API configuratie: %s", e)
        return text, {}

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

    functieomschrijving_text = functieomschrijving.get_text(separator='\n', strip=True) if functieomschrijving else "Geen omschrijving beschikbaar."
    verbeterde_functieomschrijving, token_usage = correct_markdown_with_llm(functieomschrijving_text)

    if token_usage:
        logger.info("Token gebruik - Input: %d, Output: %d, Totaal: %d",
                   token_usage['input_tokens'],
                   token_usage['output_tokens'],
                   token_usage['total_tokens'])

    markdown_output += "\n## Functieomschrijving\n" + verbeterde_functieomschrijving + "\n\n"

    return markdown_output

def check_environment_variables():
    """Controleert of alle benodigde environment variabelen zijn ingesteld."""
    logger = logging.getLogger(__name__)
    required_vars = {
        'SPINWEB_USER': 'Spinweb gebruikersnaam',
        'SPINWEB_PASS': 'Spinweb wachtwoord',
        'SPINWEB_LOGIN': 'Spinweb login URL',
        'SOURCE_URL': 'Bron URL voor vacatures',
        'PROVIDER_NAME': 'Provider naam',
        'OPENAI_API_KEY': 'OpenAI API key',
        'AIRTABLE_API_KEY': 'Airtable API key',
        'AIRTABLE_BASE_ID': 'Airtable Base ID',
        'AIRTABLE_TABLE_NAME_PROCESSED': 'Airtable tabel naam voor verwerkte items',
        'AIRTABLE_TABLE_NAME_LISTINGS': 'Airtable tabel naam voor listings'
    }

    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"- {var}: {description}")

    if missing_vars:
        logger.error("Missing environment variables:")
        for var in missing_vars:
            logger.error("%s", var)
        logger.error("Make sure these variables are set in your .env file.")
        sys.exit(1)

    logger.info("All environment variables are correctly set")

async def main():
    """
    Hoofdfunctie voor de Spinweb vacancy scraper.
    
    Deze functie voert de volgende stappen uit:
    1. Setup logging met file rotation
    2. Controleert environment variabelen
    3. Configureert de crawler
    4. Voert de crawler uit op de Spinweb website
    5. Verwerkt de gevonden vacatures
    
    Raises:
        SystemExit: Als er environment variabelen missen
        Exception: Bij onverwachte fouten tijdens het scrapen
    """
    logger = setup_logging()
    logger.info("Starting vacancy scraper")

    check_environment_variables()

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

        existing_listings = airtable.get_existing_listings()
        new_listings = {link for link in vacancy_links - existing_listings
                       if int(link.split('/')[-1]) > 863693}
        new_listings = sorted(new_listings)

        if not new_listings:
            logger.info("No new listings found.")
        else:
            logger.info("Found %d new listings to process", len(new_listings))
            for listing_url in new_listings.copy():
                result = await crawler.arun(listing_url, config=crawler_run_config)
                if result.success:
                    logger.info("Crawled URL: %s", listing_url)
                    markdown_data = extract_data_from_html(result.html, listing_url)

                    try:
                        # Eerst proberen de aanvraag toe te voegen
                        airtable.add_to_airtable(markdown_data, listing_url)
                        # Alleen als dat succesvol was, markeren als verwerkt
                        airtable.add_processed_listing(listing_url)
                        logger.info("Succesvol verwerkt en gemarkeerd: %s", listing_url)
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
