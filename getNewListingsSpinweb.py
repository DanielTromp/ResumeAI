#! /usr/bin/env python3
# This script crawls Spinweb and extracts new listings, then uploads them to Nextcloud and Airtable
import asyncio
import re
import json
import os
import requests
import datetime
from pyairtable import Api
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from playwright.async_api import Page, BrowserContext
import openai

# Load environment variables
load_dotenv()
USER = os.getenv("SPINWEB_USER")
PASSWORD = os.getenv("SPINWEB_PASS")
NEXTCLOUD_URL = "https://nextcloud.trmp.cc/remote.php/dav/files/"
NEXTCLOUD_USER = os.getenv("NEXTCLOUD_USER")
NEXTCLOUD_PASS = os.getenv("NEXTCLOUD_PASS")
NEXTCLOUD_FOLDER = "ResumeAI"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
SOURCE_URL = os.getenv("SOURCE_URL")
PROVIDER_NAME = os.getenv("PROVIDER_NAME", "provider")


def add_to_airtable(markdown_data, listing_url):
    """Adds a new listing to Airtable."""
    api = Api(AIRTABLE_API_KEY)
    table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)
    
    # Rest of the function remains the same
    lines = markdown_data.split('\n')
    data = {
        'URL': listing_url,
        'Status': 'New'  # Default status
    }
    
    # Extract information from markdown lines
    for line in lines:
        if line.startswith('- **'):
            key_value = line.replace('- **', '').split(':** ')
            if len(key_value) == 2:
                key, value = key_value
                
                # Map the fields to Airtable columns
                if key == 'Functie':
                    data['Functie'] = value
                elif key == 'Klant':
                    data['Klant'] = value
                elif key == 'Branche':
                    data['Branche'] = value
                elif key == 'Regio':
                    data['Regio'] = value
                elif key == 'Uren':
                    data['Uren'] = value
                elif key == 'Tarief':
                    data['Tarief'] = value
                elif key == 'Geplaatst':
                    try:
                        date_obj = datetime.datetime.strptime(value, '%d-%m-%Y')
                        data['Geplaatst'] = date_obj.strftime('%Y-%m-%d')
                    except:
                        data['Geplaatst'] = value
                elif key == 'Sluiting':
                    try:
                        date_obj = datetime.datetime.strptime(value, '%d-%m-%Y')
                        data['Sluiting'] = date_obj.strftime('%Y-%m-%d')
                    except:
                        data['Sluiting'] = value

    # Extract functieomschrijving
    sections = markdown_data.split('## Functieomschrijving')
    if len(sections) > 1:
        # Neem de laatste sectie (na de laatste "## Functieomschrijving")
        functieomschrijving = sections[-1].strip()
        data['Functieomschrijving'] = functieomschrijving

    try:
        table.create(data)
        print(f"Successfully added listing {listing_url} to Airtable")
    except Exception as e:
        print(f"Error adding listing to Airtable: {e}")

def nextcloud_upload(file_name, data, is_json=True):
    """Uploads a file to Nextcloud, allowing overwriting."""
    url = f"{NEXTCLOUD_URL}{NEXTCLOUD_USER}/{NEXTCLOUD_FOLDER}/{file_name}"
    headers = {"Content-Type": "application/json"} if is_json else {}
    content = json.dumps(data, indent=4) if is_json else data
    response = requests.put(url, auth=(NEXTCLOUD_USER, NEXTCLOUD_PASS), data=content, headers=headers)
    if response.status_code in [200, 201, 204]:
        print(f"Successfully uploaded {file_name} to Nextcloud")
    else:
        print(f"Error uploading {file_name} to Nextcloud: {response.status_code} - {response.text}")

def nextcloud_download(file_name):
    """Downloads a file from Nextcloud."""
    url = f"{NEXTCLOUD_URL}{NEXTCLOUD_USER}/{NEXTCLOUD_FOLDER}/{file_name}"
    response = requests.get(url, auth=(NEXTCLOUD_USER, NEXTCLOUD_PASS))
    if response.status_code == 200:
        return json.loads(response.text) if file_name.endswith(".json") else response.text
    elif response.status_code == 404:
        print(f"{file_name} not found in Nextcloud. Returning empty data.")
        return []
    else:
        print(f"Error downloading {file_name} from Nextcloud: {response.status_code} - {response.text}")
        return []

def correct_markdown_with_llm(text):
    """Uses OpenAI LLM (GPT-4o) to correct and improve markdown formatting."""
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Je bent een assistent die markdown corrigeert en verbetert, zonder feedback te geven en de tekst niet in een eigen markdown blok zetten."},
                {"role": "user", "content": f"Corrigeer en verbeter de volgende markdown:\n{text}\n\nGecorrigeerde markdown:"}
            ],
            max_tokens=4000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"An error occurred: {e}")
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
        # Opschonen van de Uren waarde
        if key == "Uren":
            value = value.replace("onbekend", "").strip()
        markdown_output += f"- **{key}:** {value}\n"
    
    functieomschrijving_text = functieomschrijving.get_text(separator='\n', strip=True) if functieomschrijving else "Geen omschrijving beschikbaar."
    verbeterde_functieomschrijving = correct_markdown_with_llm(functieomschrijving_text)
    markdown_output += "\n## Functieomschrijving\n" + verbeterde_functieomschrijving + "\n\n"
    
    return markdown_output

async def main():
    print("🔗 Starting vacancy scraper")

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
            await page.goto("https://spinweb.nl/inloggen/form", timeout=10000)
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

    # Crawl URLs to find new listings
    if not SOURCE_URL:
        print("Error: No source URL configured in environment variables.")
        return

    result = await crawler.arun(SOURCE_URL, config=crawler_run_config)
    if result.success:
        print("\nCrawled URL:", result.url)
        print("HTML length:", len(result.html))
        vacancy_links = set(f"https://{PROVIDER_NAME}" + link for link in re.findall(r'/aanvraag/\d+', result.html))
        
        existing_listings = set(nextcloud_download(f"{PROVIDER_NAME}/listings.json"))
        new_listings = sorted(vacancy_links - existing_listings, reverse=True)[:10]

        if not new_listings:
            print("No new listings found.")
        else:
            processed_listings = nextcloud_download(f"{PROVIDER_NAME}/listings.json")
            if not isinstance(processed_listings, list):
                processed_listings = []
            for listing_url in new_listings.copy():
                result = await crawler.arun(listing_url, config=crawler_run_config)
                if result.success:
                    print(f"Crawled URL: {listing_url}")
                    markdown_data = extract_data_from_html(result.html, listing_url)
                    
                    # Upload to Nextcloud
                    md_file_name = f"{PROVIDER_NAME}/aanvragen/{listing_url.split('/')[-1]}.md"
                    nextcloud_upload(md_file_name, markdown_data, is_json=False)
                    
                    # Add to Airtable
                    add_to_airtable(markdown_data, listing_url)
                    
                    processed_listings.append(listing_url)
                    new_listings.remove(listing_url)
                else:
                    print(f"Error crawling {listing_url}: {result.error_message}")
            nextcloud_upload(f"{PROVIDER_NAME}/listings.json", processed_listings)

    await crawler.close()

if __name__ == "__main__":
    asyncio.run(main())

# End of script
