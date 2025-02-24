#!/usr/bin/env python3
"""
Spinweb.nl Vacancy Scraper

This script crawls the Spinweb.nl website to find new vacancies and upload them to NocoDB.
It performs the following tasks:
1. Login to Spinweb.nl
2. Get new vacancy listings
3. Compare with existing listings in NocoDB
4. Extract vacancy details
5. Upload new vacancies to NocoDB

Author: Daniel Tromp
Email: drpgmtromp@gmail.com
Version: 0.0.1
Created: 2025-02-11
Updated: 2025-02-17
License: MIT
Repository: https://github.com/DanielTromp/ResumeAI
"""

# Standard library imports
import asyncio
import logging
import logging.handlers
import re

# Third-party imports
import html2text
import playwright.async_api
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

# Project specific imports
from config import *
#from components.airtable_client import AirtableClient
from components.nocodb_client import NocoDBClient

def convert_html_to_markdown(html_text: str) -> str:
    """Convert HTML to Markdown while preserving the formatting."""
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = False
    converter.body_width = 0
    markdown_text = converter.handle(html_text)
    return markdown_text.strip()

# Configure logging
def setup_logging() -> logging.Logger:
    """Setup logging with file rotation."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Remove existing handlers to prevent duplicate logging
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler with rotation
    log_file = 'spinweb_scraper.log'
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger

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
        'URL1_SOURCE': URL1_SOURCE
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

def normalize_url(url: str) -> str:
    """Normaliseert een URL door trailing slashes te verwijderen en naar kleine letters om te zetten."""
    return url.rstrip('/').lower()

async def main():
    """
    Main function for the Spinweb vacancy scraper.
    
    This function performs the following steps:
    1. Setup logging with file rotation
    2. Checks environment variables
    3. Deletes closed listings
    4. Configures the crawler
    5. Runs the crawler on the Spinweb website
    6. Processes the found vacancies
    """
    logger = setup_logging()
    logger.info("Starting vacancy scraper")
    
    check_environment_variables()
    
    # Initialize NocoDB client
    nocodb = NocoDBClient()
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
        """Hook for setting up the page and context after creation.
        
        Args:
            page: The Playwright Page instance
            browser_context: Optional BrowserContext parameter
            **kwargs: Extra keyword arguments passed by crawl4ai
        
        Returns:
            The configured Page instance
        """
        logger = logging.getLogger(__name__)
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
        return

    result = await crawler.arun(URL1_SOURCE, config=crawler_run_config)
    if result.success:
        logger.info("Crawled URL: %s", result.url)
        soup = BeautifulSoup(result.html, 'html.parser')
        
        # Zoek alle vacature links
        vacancy_links = set()
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/aanvraag/' in href:
                full_url = f"https://{URL1_PROVIDER_NAME}{href}" if href.startswith('/') else href
                vacancy_links.add(full_url)
        
        logger.info(f"Found {len(vacancy_links)} vacancy links")
        
        # Bouw vacancy_links en normaliseer ze
        vacancy_links = {normalize_url(link) for link in vacancy_links}

        # Normaliseer bestaande listings uit NocoDB
        existing_aanvragen_urls = {normalize_url(url) for url in nocodb.get_existing_listings()}
        lowest_url = normalize_url(nocodb.get_lowest_listing_url())

        # Filter new listings
        new_listings = {link for link in vacancy_links
                        if link not in existing_aanvragen_urls and link > lowest_url}
        new_listings = sorted(new_listings)

        logger.info(f"Found {len(new_listings)} new vacancies to process")
        for listing_url in new_listings.copy():
            result = await crawler.arun(listing_url, config=crawler_run_config)
            if result.success:
                logger.info("Crawled URL: %s", listing_url)
                markdown_data = extract_data_from_html(result.html, listing_url)
                
                # NocoDB addition with error handling in the module
                nocodb.add_to_nocodb(markdown_data, listing_url)
                new_listings.remove(listing_url)
            else:
                logger.error("Error crawling %s: %s", listing_url, result.error_message)

            # TODO: Remove this after testing
            #exit()
    else:
        logger.error("Error crawling source URL: %s", result.error_message)

    await crawler.close()

if __name__ == "__main__":
    asyncio.run(main())

# End of script
