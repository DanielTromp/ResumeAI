#!/usr/bin/env python3
"""
Spinweb.nl Vacancy Scraper

Dit script crawlt de Spinweb.nl website om nieuwe vacatures te vinden 
en slaat deze lokaal op in een CSV-bestand. De vacatures worden eerst 
omgezet naar Markdown.

Author: Daniel Tromp
Email: drpgmtromp@gmail.com
Version: 1.0.0
Created: 2025-02-11
Updated: 2025-02-17
License: MIT
"""

import asyncio
import logging
import logging.handlers
import re
import os
import csv
import datetime
from typing import Tuple, Dict, Set

import html2text
import playwright.async_api
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

from config import *

# Gebruik de CSV-export zoals gegeven als basis
CSV_VACATURES = "vacancies.csv"
CSV_HEADERS = [
    "URL", "Status", "Functie", "Klant", "Regio", "Uren",
    "Geplaatst", "Sluiting", "Functieomschrijving", "Top_Match",
    "Match Toelichting", "Checked_resumes", "Tarief", "Branche"
]

def convert_html_to_markdown(html_text: str) -> str:
    """Zet HTML om naar Markdown."""
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = False
    converter.body_width = 0
    return converter.handle(html_text).strip()

def parse_date(value: str) -> str:
    """Zet een datum string om naar het juiste formaat."""
    try:
        # Probeer verschillende datumformaten
        for fmt in ['%d-%m-%Y', '%B %d, %Y', '%Y-%m-%d']:
            try:
                date_obj = datetime.datetime.strptime(value, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        return value
    except Exception as e:
        logging.error(f"Fout bij parsen van datum: {e}")
        return value

def get_existing_listings() -> Set[str]:
    """Haalt bestaande listings op uit het CSV-bestand."""
    ensure_csv_exists()
    existing_urls = set()
    print(CSV_VACATURES)
    try:
        with open(CSV_VACATURES, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            existing_urls = {row['URL'] for row in reader if row.get('URL')}
    except Exception as e:
        logging.error(f"Fout bij ophalen bestaande listings: {e}")
    return existing_urls

def get_lowest_listing_url() -> str:
    """Haalt de URL met de laagste waarde op uit het CSV-bestand."""
    ensure_csv_exists()
    try:
        with open(CSV_VACATURES, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            urls = [row['URL'] for row in reader if row.get('URL')]
            if not urls:
                return "https://spinweb.nl/aanvraag/866345"  # Fallback URL
            return min(urls)
    except Exception as e:
        logging.error(f"Fout bij ophalen laagste URL: {e}")
        return "https://spinweb.nl/aanvraag/866345"  # Fallback URL

def extract_data_from_html(html, url) -> Tuple[str, Dict[str, str]]:
    """Extraheert gestructureerde data uit HTML en zet om naar Markdown."""
    soup = BeautifulSoup(html, "html.parser")
    
    functie = soup.select_one(".title-page--text")
    klant = soup.select_one(".application-customer .dynamic-truncate")
    functieomschrijving = soup.select_one(".application-content")

    # Verzamel alle aanvraag info
    aanvraag_info = {}
    for item in soup.select(".application-info--item"):
        label = item.select_one(".application-info--label")
        value = item.select_one(".application-info--value")
        if label and value:
            key = label.get_text(strip=True)
            val = value.get_text(strip=True)
            aanvraag_info[key] = val

    # Bouw markdown output
    markdown_output = "## Aanvraag Informatie\n"
    markdown_output += f"- [🔗 Aanvraag Link]({url})\n"
    markdown_output += "- **Functie:** " + (functie.get_text(strip=True) if functie else "Onbekend") + "\n"
    markdown_output += "- **Klant:** " + (klant.get_text(strip=True) if klant else "Onbekend") + "\n"
    
    # Extraheer specifieke velden voor CSV
    extracted_data = {
        'URL': url,
        'Status': 'Nieuw',
        'Functie': functie.get_text(strip=True) if functie else "Onbekend",
        'Klant': klant.get_text(strip=True) if klant else "Onbekend",
        'Regio': aanvraag_info.get('Regio', ''),
        'Uren': aanvraag_info.get('Uren', '').replace('onbekend', '').strip(),
        'Geplaatst': parse_date(aanvraag_info.get('Geplaatst', '')),
        'Sluiting': parse_date(aanvraag_info.get('Sluiting', '')),
        'Tarief': aanvraag_info.get('Tarief', ''),
        'Branche': aanvraag_info.get('Branche', 'ICT')
    }

    # Voeg overige info toe aan markdown
    for key, value in aanvraag_info.items():
        if key == "Uren":
            value = value.replace("onbekend", "").strip()
        markdown_output += f"- **{key}:** {value}\n"

    if functieomschrijving:
        functieomschrijving_html = str(functieomschrijving)
    else:
        functieomschrijving_html = "<p>No description available.</p>"

    markdown_functieomschrijving = convert_html_to_markdown(functieomschrijving_html)
    markdown_output += "\n## Functieomschrijving\n" + markdown_functieomschrijving + "\n\n"
    
    # Voeg functieomschrijving toe aan extracted_data
    extracted_data['Functieomschrijving'] = markdown_output
    
    return markdown_output, extracted_data

def ensure_csv_exists():
    """Controleer of het CSV-bestand bestaat; zo niet, maak het aan met de juiste headers."""
    if not os.path.exists(CSV_VACATURES):
        os.makedirs(os.path.dirname(CSV_VACATURES), exist_ok=True)
        with open(CSV_VACATURES, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
            writer.writeheader()

def append_vacancy_to_csv(data: Dict[str, str]) -> None:
    """Voegt een nieuwe vacature toe aan het CSV-bestand."""
    ensure_csv_exists()
    try:
        # Controleer of het bestand leeg is of alleen een header heeft
        is_new_file = os.path.getsize(CSV_VACATURES) <= len(','.join(CSV_HEADERS)) + 2

        with open(CSV_VACATURES, mode='a', encoding='utf-8') as csvfile:  # Verwijderd newline=''
            writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
            writer.writerow(data)
            
    except Exception as e:
        logging.error(f"Fout bij toevoegen vacature aan CSV: {e}")

def setup_logging() -> logging.Logger:
    """Stelt logging in met rotatie."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
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

async def main():
    """Hoofdfunctie voor de Spinweb vacancy scraper."""
    logger = setup_logging()
    logger.info("Starting vacancy scraper")
    
    # Configureer de crawler
    browser_config = BrowserConfig(headless=True, verbose=True)
    crawler_run_config = CrawlerRunConfig(
        js_code="window.scrollTo(0, document.body.scrollHeight);",
        wait_for="body",
        cache_mode=CacheMode.BYPASS
    )
    crawler = AsyncWebCrawler(config=browser_config, request_timeout=30000)
    
    async def on_page_context_created(page: playwright.async_api.Page, 
                                      browser_context: playwright.async_api.BrowserContext = None, 
                                      **kwargs):
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
                await page.wait_for_load_state("networkidle", timeout=10000)
            else:
                logger.info("Already logged in, skipping login step.")
        except Exception as e:
            logger.error("Fout tijdens login: %s", e)
        return page

    crawler.crawler_strategy.set_hook("on_page_context_created", on_page_context_created)
    await crawler.start()

    if not URL1_SOURCE:
        logger.error("Error: Geen source URL geconfigureerd.")
        return

    result = await crawler.arun(URL1_SOURCE, config=crawler_run_config)
    if result.success:
        logger.info("Crawled URL: %s", result.url)
        vacancy_links = set(f"https://{URL1_PROVIDER_NAME}" + link 
                          for link in re.findall(r'/aanvraag/\d+', result.html))
        
        existing_urls = get_existing_listings()
        lowest_url = get_lowest_listing_url()
        
        # Filter nieuwe listings op basis van bestaande URLs en laagste URL
        new_listings = {link for link in vacancy_links
                       if link not in existing_urls
                       and link > lowest_url}
        new_listings = sorted(new_listings)
        
        logger.info(f"Found {len(new_listings)} new vacancies to process")
        for listing_url in new_listings.copy():
            result_listing = await crawler.arun(listing_url, config=crawler_run_config)
            if result_listing.success:
                logger.info("Crawled URL: %s", listing_url)
                markdown_data, extracted_data = extract_data_from_html(
                    result_listing.html, listing_url)
                append_vacancy_to_csv(extracted_data)
                logger.info(f"Added vacancy to CSV: {listing_url}")
            else:
                logger.error("Error crawling %s: %s", listing_url, result_listing.error_message)
    else:
        logger.error("Error crawling source URL: %s", result.error_message)

    await crawler.close()

if __name__ == "__main__":
    asyncio.run(main()) 