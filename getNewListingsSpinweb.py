#! /usr/bin/env python3
# This script crawls Spinweb and extracts new listings and uploads them to Airtable
import asyncio
import re
import os
import datetime
from pyairtable import Api
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from playwright.async_api import Page, BrowserContext
import openai
import sys

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

class AirtableClient:
    """Centrale class voor Airtable interacties."""
    def __init__(self):
        self.api = Api(AIRTABLE_API_KEY)
        self.listings_table = self.api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME_LISTINGS)
        self.processed_table = self.api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME_PROCESSED)

    def sanitize_url(self, url: str) -> str:
        """Maakt URL veilig voor gebruik in Airtable formules."""
        return url.replace("'", "\\'")

    def get_existing_listings(self) -> set:
        """Haalt bestaande listings op uit Airtable."""
        try:
            records = self.listings_table.all()
            listings = {record['fields']['Listing'] 
                       for record in records 
                       if 'Listing' in record['fields']}

            print(f"Found {len(listings)} existing listings")
            return listings

        except Exception as e:
            print(f"Error getting existing listings from Airtable: {e}")
            return set()

    def add_processed_listing(self, listing_url: str) -> None:
        """Voegt een verwerkte listing URL toe aan Airtable."""
        try:
            self.listings_table.create({"Listing": listing_url})
            print(f"Added {listing_url} to processed listings")
        except Exception as e:
            print(f"Error adding listing to processed listings: {e}")

    def add_or_update_listing(self, markdown_data: str, listing_url: str) -> None:
        """Voegt een nieuwe listing toe of werkt bestaande bij in Airtable."""
        data = {
            'Listing': listing_url
        }

        try:
            # Gebruik gesaniteerde URL in de formule
            safe_url = self.sanitize_url(listing_url)
            existing_records = self.listings_table.all(
                formula=f"FIND('{safe_url}', {{Listing}})"
            )

            if existing_records:
                record_id = existing_records[0]['id']
                self.listings_table.update(record_id, data)
                print(f"Successfully updated listing {listing_url} in Airtable")
            else:
                self.listings_table.create(data)
                print(f"Successfully added listing {listing_url} to Airtable")
        except Exception as e:
            print(f"Error adding/updating listing to Airtable: {e}")

    def get_table_schema(self) -> None:
        """Debug functie om tabel structuur te printen."""
        try:
            record = self.listings_table.first()
            if record:
                print("Available fields:", record['fields'].keys())
            else:
                print("No records found in table")
        except Exception as e:
            print(f"Error getting table schema: {e}")

    def add_to_airtable(self, markdown_data: str, listing_url: str) -> None:
        """Voegt een nieuwe aanvraag toe aan de Aanvragen tabel."""
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
                            print(f"Fout bij parsen van datum 'Geplaatst': {e}")
                            data['Geplaatst'] = value
                    elif key == 'Sluiting':
                        try:
                            date_obj = datetime.datetime.strptime(value, '%d-%m-%Y')
                            data['Sluiting'] = date_obj.strftime('%Y-%m-%d')
                        except ValueError as e:
                            print(f"Fout bij parsen van datum 'Sluiting': {e}")
                            data['Sluiting'] = value

        sections = markdown_data.split('## Functieomschrijving')
        if len(sections) > 1:
            functieomschrijving = sections[-1].strip()
            data['Functieomschrijving'] = functieomschrijving

        try:
            # Zoek bestaande record met dezelfde URL
            safe_url = self.sanitize_url(listing_url)
            existing_records = self.processed_table.all(
                formula=f"FIND('{safe_url}', {{URL}})"
            )

            if existing_records:
                record_id = existing_records[0]['id']
                self.processed_table.update(record_id, data)
                print(f"Successfully updated aanvraag {listing_url} in Airtable")
            else:
                self.processed_table.create(data)
                print(f"Successfully added aanvraag {listing_url} to Airtable")
        except Exception as e:
            print(f"Error adding/updating aanvraag to Airtable: {e}")

def get_table_schema():
    """Debug function to print table structure."""
    api = Api(AIRTABLE_API_KEY)
    table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME_PROCESSED)

    try:
        record = table.first()
        if record:
            print("Available fields:", record['fields'].keys())
        else:
            print("No records found in table")
    except Exception as e:
        print(f"Error getting table schema: {e}")

def get_existing_listings():
    """Get list of already processed listings from Airtable."""
    api = Api(AIRTABLE_API_KEY)
    table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME_LISTINGS)

    try:
        # Haal alle records op
        records = table.all()
        # Verzamel listings
        listings = {record['fields']['Listing'] 
                   for record in records 
                   if 'Listing' in record['fields']}

        print(f"Found {len(listings)} existing listings")
        return listings

    except Exception as e:
        print(f"Error getting existing listings from Airtable: {e}")
        return set()

def add_processed_listing(listing_url):
    """Add a processed listing URL to Airtable."""
    api = Api(AIRTABLE_API_KEY)
    table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME_LISTINGS)

    try:
        table.create({"Listing": listing_url})
        print(f"Added {listing_url} to processed listings")
    except Exception as e:
        print(f"Error adding listing to processed listings: {e}")

def add_to_airtable(markdown_data, listing_url):
    """Adds or updates a listing in Airtable."""
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
                        print(f"Fout bij parsen van datum 'Geplaatst': {e}")
                        data['Geplaatst'] = value
                elif key == 'Sluiting':
                    try:
                        date_obj = datetime.datetime.strptime(value, '%d-%m-%Y')
                        data['Sluiting'] = date_obj.strftime('%Y-%m-%d')
                    except:
                        data['Sluiting'] = value

    sections = markdown_data.split('## Functieomschrijving')
    if len(sections) > 1:
        functieomschrijving = sections[-1].strip()
        data['Functieomschrijving'] = functieomschrijving

    try:
        # Zoek bestaande record met dezelfde URL
        existing_records = table.all(formula=f"URL = '{listing_url}'")

        if existing_records:
            # Update bestaande record
            record_id = existing_records[0]['id']
            table.update(record_id, data)
            print(f"Successfully updated listing {listing_url} in Airtable")
        else:
            # Maak nieuwe record
            table.create(data)
            print(f"Successfully added listing {listing_url} to Airtable")
    except Exception as e:
        print(f"Error adding/updating listing to Airtable: {e}")

def correct_markdown_with_llm(text: str) -> str:
    """Corrigeert de markdown-opmaak met behulp van het OpenAI API."""
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
        
        # Token gebruik bijhouden
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
        
        print(f"Token gebruik - Input: {input_tokens}, Output: {output_tokens}, Totaal: {total_tokens}")
        
        return response.choices[0].message.content.strip()
    except openai.APIError as e:
        print(f"OpenAI API Error: {e}")
        return text
    except openai.RateLimitError as e:
        print(f"OpenAI Rate Limit bereikt: {e}")
        return text
    except openai.APITimeoutError as e:
        print(f"OpenAI Timeout: {e}")
        return text
    except openai.APIConnectionError as e:
        print(f"OpenAI Connectie probleem: {e}")
        return text
    except Exception as e:
        print(f"Onverwachte fout bij OpenAI request: {e}")
        return text

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

    functieomschrijving_text = functieomschrijving.get_text(separator='\n', strip=True) if functieomschrijving else "Geen omschrijving beschikbaar."
    verbeterde_functieomschrijving = correct_markdown_with_llm(functieomschrijving_text)
    markdown_output += "\n## Functieomschrijving\n" + verbeterde_functieomschrijving + "\n\n"

    return markdown_output

def check_environment_variables():
    """Controleert of alle vereiste environment variables zijn ingesteld."""
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
        print("❌ Ontbrekende environment variables:")
        print("\n".join(missing_vars))
        print("\nZorg dat deze variabelen zijn ingesteld in je .env bestand.")
        sys.exit(1)

    print("✅ Alle environment variables zijn correct ingesteld")

async def main():
    print("🔗 Starting vacancy scraper")

    # Controleer environment variables voordat we beginnen
    check_environment_variables()

    # Initialiseer Airtable client
    airtable = AirtableClient()
    airtable.get_table_schema()

    md_generator = DefaultMarkdownGenerator(
        options={
            "ignore_images": True
        }
    )

    browser_config = BrowserConfig(
        headless=True,
        verbose=True
    )

    crawler_run_config = CrawlerRunConfig(
        markdown_generator=md_generator,
        js_code="window.scrollTo(0, document.body.scrollHeight);",
        wait_for="body",
        cache_mode=CacheMode.BYPASS
    )

    crawler = AsyncWebCrawler(config=browser_config, request_timeout=30000)

    async def on_page_context_created(page: Page, context: BrowserContext, **kwargs):
        print("[HOOK] Setting up page & context.")
        try:
            await page.goto(LOGIN_URL, timeout=10000)
        except Exception as e:
            print(f"Error loading login page: {e}")
            return page
        if await page.is_visible("input[name='user']"):
            print("Logging in...")
            await page.fill("input[name='user']", USER)
            await page.fill("input[name='pass']", PASSWORD)
            await page.click("button[type='submit']")
            await page.wait_for_load_state("networkidle", timeout=10000)
        else:
            print("Already logged in, skipping login step.")
        return page

    crawler.crawler_strategy.set_hook("on_page_context_created", on_page_context_created)

    await crawler.start()

    if not SOURCE_URL:
        print("Error: No source URL configured in environment variables.")
        return

    result = await crawler.arun(SOURCE_URL, config=crawler_run_config)
    if result.success:
        print("\nCrawled URL:", result.url)
        vacancy_links = set(f"https://{PROVIDER_NAME}" + link for link in re.findall(r'/aanvraag/\d+', result.html))

        existing_listings = airtable.get_existing_listings()
        # Filter op basis van referentie nummer 863660
        new_listings = {link for link in vacancy_links - existing_listings
                       if int(link.split('/')[-1]) > 863693}
        new_listings = sorted(new_listings)  # Sorteer van oud naar nieuw

        if not new_listings:
            print("No new listings found.")
        else:
            print(f"Found {len(new_listings)} new listings to process")
            for listing_url in new_listings.copy():
                result = await crawler.arun(listing_url, config=crawler_run_config)
                if result.success:
                    print(f"Crawled URL: {listing_url}")
                    markdown_data = extract_data_from_html(result.html, listing_url)

                    # Add to both tables
                    airtable.add_or_update_listing(markdown_data, listing_url)
                    airtable.add_to_airtable(markdown_data, listing_url)
                    airtable.add_processed_listing(listing_url)

                    new_listings.remove(listing_url)
                else:
                    print(f"Error crawling {listing_url}: {result.error_message}")

    await crawler.close()

if __name__ == "__main__":
    asyncio.run(main())

# End of script
