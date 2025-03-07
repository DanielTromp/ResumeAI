"""
NocoDB client

Author: Daniel Tromp
Email: drpgmtromp@gmail.com
Version: 0.0.2
Created: 2025-02-24
Updated: 2025-05-26
License: MIT
Repository: https://github.com/DanielTromp/ResumeAI
"""

import os
import json
import datetime
import logging
import requests
import re
import time
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Get NocoDB configuration from environment
NOCODB_TOKEN = os.getenv("NOCODB_TOKEN")
NOCODB_URL = os.getenv("NOCODB_URL")
NOCODB_PROJECT = os.getenv("NOCODB_PROJECT")
NOCODB_TABLE = os.getenv("NOCODB_TABLE")

# Check if we have all required config
if all([NOCODB_TOKEN, NOCODB_URL, NOCODB_PROJECT, NOCODB_TABLE]):
    # Constants voor NocoDB
    # NocoDB v0.90+ uses this format
    NOCODB_API_URL = f"{NOCODB_URL}/api/v1/db/data/v1/{NOCODB_PROJECT}/{NOCODB_TABLE}"
    
    # Set up multiple possible API URLs to try (different NocoDB versions use different formats)
    NOCODB_API_URLs = [
        f"{NOCODB_URL}/api/v1/db/data/v1/{NOCODB_PROJECT}/{NOCODB_TABLE}",  # v0.90+
        f"{NOCODB_URL}/api/v1/db/data/noco/{NOCODB_PROJECT}/{NOCODB_TABLE}", # Later versions
        f"{NOCODB_URL}/api/v2/tables/{NOCODB_TABLE}/records"  # Possible v2 API
    ]
    
    NOCODB_HEADERS = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "xc-token": NOCODB_TOKEN
    }
    
    # Also try with 'xc-auth' as some versions use this instead of 'xc-token'
    NOCODB_HEADERS_ALT = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "xc-auth": NOCODB_TOKEN
    }
else:
    # Set defaults to avoid errors
    NOCODB_API_URL = ""
    NOCODB_API_URLs = []
    NOCODB_HEADERS = {}
    NOCODB_HEADERS_ALT = {}

class NocoDBClient:
    """Centrale class voor NocoDB interacties."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.WARNING)
        # Add console handler if not already present
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # Default values
        self.api_endpoint = NOCODB_API_URL
        self.headers = NOCODB_HEADERS
        self.api_urls = NOCODB_API_URLs
        
        # Only attempt to connect if all required config is present
        if all([NOCODB_TOKEN, NOCODB_URL, NOCODB_PROJECT, NOCODB_TABLE]):
            # Try to find a working API endpoint from the possible URLs
            connection_success = False
            
            # First try with the default headers
            for api_url in self.api_urls:
                try:
                    self.logger.warning(f"Trying NocoDB connection with URL: {api_url}")
                    response = requests.get(api_url, headers=self.headers)
                    if response.ok:
                        self.api_endpoint = api_url
                        self.logger.warning(f"✅ NocoDB connection successful with URL: {api_url}")
                        connection_success = True
                        break
                    else:
                        self.logger.warning(f"❌ NocoDB connection failed with URL: {api_url}, status: {response.status_code}")
                        self.logger.warning(f"Response: {response.text}")
                except Exception as e:
                    self.logger.warning(f"❌ Error connecting to {api_url}: {e}")
            
            # If no success, try with alternative headers
            if not connection_success:
                for api_url in self.api_urls:
                    try:
                        self.logger.warning(f"Trying NocoDB connection with URL: {api_url} and alternative headers")
                        response = requests.get(api_url, headers=NOCODB_HEADERS_ALT)
                        if response.ok:
                            self.api_endpoint = api_url
                            self.headers = NOCODB_HEADERS_ALT
                            self.logger.warning(f"✅ NocoDB connection successful with URL: {api_url} and alternative headers")
                            connection_success = True
                            break
                        else:
                            self.logger.warning(f"❌ NocoDB connection failed with URL: {api_url} and alternative headers, status: {response.status_code}")
                    except Exception as e:
                        self.logger.warning(f"❌ Error connecting to {api_url} with alternative headers: {e}")
            
            if not connection_success:
                self.logger.error(f"❌ Could not connect to NocoDB with any combination of URLs and headers")
                # Try to get NocoDB server info to understand the version
                try:
                    info_url = f"{NOCODB_URL}/api/v1/version"
                    info_response = requests.get(info_url)
                    if info_response.ok:
                        self.logger.warning(f"NocoDB version info: {info_response.text}")
                except:
                    pass
        else:
            self.logger.warning("⚠️ NocoDB configuration incomplete - some operations may fail")

    def debug_connection(self):
        """Debug functie om de verbinding en tabelstructuur te testen."""
        try:
            # Test een simpele query
            params = {"limit": 1}
            response = requests.get(self.api_endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()

            # Alleen debug output als het logging niveau DEBUG is
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug("API Response structure:")
                self.logger.debug(json.dumps(data, indent=2))

                if data.get("list"):
                    self.logger.debug("Beschikbare kolommen:")
                    for key in data["list"][0].keys():
                        self.logger.debug(f"- {key}")
                else:
                    self.logger.warning("Geen records gevonden in tabel")

        except Exception as e:
            self.logger.error(f"Debug connectie fout: {str(e)}")

    @staticmethod
    def normalize_url(url: str) -> str:
        """Normaliseert een URL voor consistente vergelijking in de database."""
        # Verwijder witruimte aan begin en eind
        url = url.strip()

        # Zet om naar kleine letters
        url = url.lower()

        # Verwijder eventuele trailing slashes
        url = url.rstrip('/')

        # Verwijder 'http://' of 'https://' prefix
        url = url.replace('http://', '').replace('https://', '')

        # Verwijder 'www.' prefix als die aanwezig is
        url = url.replace('www.', '')

        # Verwijder eventuele parameters of ankers
        if '?' in url:
            url = url.split('?')[0]
        if '#' in url:
            url = url.split('#')[0]
            
        return url

    @staticmethod
    def normalize_url_for_crawler(url: str) -> str:
        """Normaliseert een URL voor gebruik in de crawler (behoudt protocol)."""
        # Verwijder witruimte aan begin en eind
        url = url.strip()

        # Zet om naar kleine letters
        url = url.lower()

        # Verwijder eventuele trailing slashes
        url = url.rstrip('/')

        # Zorg ervoor dat de URL begint met https://
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url

        # Verwijder eventuele parameters of ankers
        if '?' in url:
            url = url.split('?')[0]
        if '#' in url:
            url = url.split('#')[0]
            
        return url

    def update_record(self, data: dict, listing_url: str, vacancy_id: int = None) -> bool:
        """Update een record in NocoDB op basis van de URL."""
        try:
            # Log de input parameters
            self.logger.debug("Update record aangeroepen met:")
            self.logger.debug(f"Originele URL: {listing_url}")
            self.logger.debug(f"Data: {json.dumps(data, indent=2)}")
            
            if not self.api_endpoint:
                self.logger.error("No valid API endpoint found for NocoDB")
                return False
            
            # Normaliseer de URL voor zowel de zoekopdracht als de data
            normalized_url = self.normalize_url(listing_url)
            
            # Prepare multiple where formats to try (different NocoDB versions use different formats)
            where_formats = [
                {"where": f"(URL,eq,{normalized_url})"},
                {"where": f"(URL,eq,'{normalized_url}')"},
                {"filter": f"URL={normalized_url}"},
                {"filter": f"URL='{normalized_url}'"},
                {"w": f"URL,eq,{normalized_url}"},
                {"w": f"URL,eq,'{normalized_url}'"}
            ]
            
            records = []
            record_response = None
            
            # Try each where format until we find records
            for params in where_formats:
                self.logger.info(f"Trying to find record with params: {params}")
                try:
                    response = requests.get(self.api_endpoint, headers=self.headers, params=params)
                    if response.ok:
                        record_response = response
                        # Try to extract records from various response formats
                        resp_data = response.json()
                        if isinstance(resp_data, list):
                            records = resp_data
                        elif isinstance(resp_data, dict):
                            if "list" in resp_data:
                                records = resp_data.get("list", [])
                            elif "data" in resp_data:
                                records = resp_data.get("data", [])
                            elif "records" in resp_data:
                                records = resp_data.get("records", [])
                            elif "rows" in resp_data:
                                records = resp_data.get("rows", [])
                            
                        if records:
                            self.logger.info(f"Found {len(records)} records with params: {params}")
                            break
                except Exception as search_error:
                    self.logger.warning(f"Error searching with params {params}: {str(search_error)}")
                    continue
            
            # If we still didn't find anything, try a different approach
            if not records and record_response is None:
                try:
                    # Try getting all records and filtering client-side
                    self.logger.info("Trying to get all records and filter client-side")
                    response = requests.get(self.api_endpoint, headers=self.headers)
                    if response.ok:
                        resp_data = response.json()
                        if isinstance(resp_data, list):
                            all_records = resp_data
                        elif isinstance(resp_data, dict):
                            if "list" in resp_data:
                                all_records = resp_data.get("list", [])
                            elif "data" in resp_data:
                                all_records = resp_data.get("data", [])
                            elif "records" in resp_data:
                                all_records = resp_data.get("records", [])
                            elif "rows" in resp_data:
                                all_records = resp_data.get("rows", [])
                            else:
                                all_records = []
                        else:
                            all_records = []
                        
                        # Filter records by URL
                        records = [r for r in all_records if r.get("URL") == normalized_url]
                        self.logger.info(f"Found {len(records)} records by client-side filtering")
                        record_response = response
                except Exception as fallback_error:
                    self.logger.warning(f"Fallback search failed: {str(fallback_error)}")
            
            self.logger.info(f"Found {len(records)} matching records")
            if records:
                self.logger.info(f"Found record details: {json.dumps(records[0], indent=2)}")
            
            if records:
                # Determine the record ID field
                record = records[0]
                record_id = None
                id_fields = ["Id", "id", "ID", "_id"]
                for field in id_fields:
                    if field in record:
                        record_id = record[field]
                        self.logger.info(f"Found ID in field '{field}': {record_id}")
                        break
                
                if not record_id:
                    self.logger.warning("No ID field found in record")
                    # Try to extract ID from a property like 'links' or '_href'
                    if "links" in record and isinstance(record["links"], list) and len(record["links"]) > 0:
                        for link in record["links"]:
                            if "rel" in link and link["rel"] == "self" and "href" in link:
                                href = link["href"]
                                # Extract ID from href
                                import re
                                id_match = re.search(r'/([^/]+)$', href)
                                if id_match:
                                    record_id = id_match.group(1)
                                    self.logger.info(f"Extracted ID from link: {record_id}")
                                    break
                
                if record_id:
                    # Try different update URL formats
                    update_urls = [
                        f"{self.api_endpoint}/{record_id}",  # Standard format
                        f"{self.api_endpoint}?id={record_id}",  # Query parameter format
                        f"{self.api_endpoint.split('?')[0]}/{record_id}"  # Strip query parameters
                    ]
                    
                    # Gebruik de genormaliseerde URL in de data
                    data["URL"] = normalized_url
                    
                    update_success = False
                    
                    # Try PUT and PATCH methods
                    for update_url in update_urls:
                        self.logger.info(f"Trying update with URL: {update_url}")
                        try:
                            # Try PUT first
                            response = requests.put(update_url, headers=self.headers, json=data)
                            if response.ok:
                                update_success = True
                                self.logger.info(f"PUT update successful with URL: {update_url}")
                                break
                            else:
                                # Try PATCH
                                self.logger.info(f"PUT failed, trying PATCH...")
                                response = requests.patch(update_url, headers=self.headers, json=data)
                                if response.ok:
                                    update_success = True
                                    self.logger.info(f"PATCH update successful with URL: {update_url}")
                                    break
                                else:
                                    self.logger.warning(f"PATCH failed too: {response.status_code} - {response.text}")
                        except Exception as update_error:
                            self.logger.warning(f"Error updating with URL {update_url}: {str(update_error)}")
                            continue
                    
                    if update_success:
                        self.logger.info(f"Record successfully updated: {normalized_url} (ID: {record_id})")
                        return True
                    else:
                        # Fall back to create
                        self.logger.warning(f"All update attempts failed, falling back to create...")
                
                # If we get here, either we couldn't find an ID, or all update attempts failed
                # Fall back to creating a new record
                
            # Create new record scenarios: 
            # 1. No matching records found
            # 2. Records found but no ID field
            # 3. Records found, ID field found, but update failed
            
            data["URL"] = normalized_url
            self.logger.info(f"Creating new record with data: {json.dumps(data, indent=2)}")
            
            # Try different create methods and URL variations
            create_urls = [self.api_endpoint] + self.api_urls
            create_success = False
            
            for create_url in create_urls:
                try:
                    response = requests.post(create_url, headers=self.headers, json=data)
                    if response.ok:
                        create_success = True
                        self.logger.info(f"Record created successfully with URL: {create_url}")
                        break
                    else:
                        self.logger.warning(f"Create failed with URL {create_url}: {response.status_code} - {response.text}")
                except Exception as create_error:
                    self.logger.warning(f"Error creating with URL {create_url}: {str(create_error)}")
                    continue
            
            if create_success:
                return True
            else:
                self.logger.error("All create attempts failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating record: {listing_url} - {str(e)}")
            self.logger.error(f"API endpoint: {self.api_endpoint}")
            self.logger.error(f"Headers: {{'accept': 'application/json', 'Content-Type': 'application/json', 'token': '***'}}")
            self.logger.exception("Stack trace:")
            
            # Laatste poging - probeer altijd een nieuw record toe te voegen bij fatale fouten
            try:
                self.logger.info("Last resort: trying to add as a new record after error")
                data["URL"] = self.normalize_url(listing_url)
                
                # Try all possible URLs
                for create_url in self.api_urls:
                    try:
                        response = requests.post(create_url, headers=self.headers, json=data)
                        if response.ok:
                            self.logger.info(f"Successfully created record as last resort with URL: {create_url}")
                            return True
                    except:
                        continue
                
                # Try alternative headers
                for create_url in self.api_urls:
                    try:
                        response = requests.post(create_url, headers=NOCODB_HEADERS_ALT, json=data)
                        if response.ok:
                            self.logger.info(f"Successfully created record with alternative headers and URL: {create_url}")
                            return True
                    except:
                        continue
                
                return False
            except Exception as inner_e:
                self.logger.error(f"Last resort attempt failed: {str(inner_e)}")
                return False

    def sanitize_url(self, url: str) -> str:
        """Maakt een URL veilig voor gebruik in NocoDB formules."""
        # Verwijder eventuele quotes
        url = url.replace("'", "")
        url = url.replace('"', "")
        
        # Escape speciale karakters
        url = url.replace('\\', '\\\\')
        url = url.replace('%', '\\%')
        url = url.replace('_', '\\_')
        
        return url

    def get_existing_listings(self) -> set:
        """Haalt alle bestaande listings op uit NocoDB met paginering."""
        listings = set()
        page = 1
        page_size = 1000  # Pas aan indien nodig
        while True:
            params = {"page": page, "pageSize": page_size}
            try:
                response = requests.get(self.api_endpoint, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                current_records = data.get("list", [])
                for record in current_records:
                    if "URL" in record:
                        listings.add(record.get("URL"))
                page_info = data.get("pageInfo", {})
                if not page_info.get("isLastPage", True):
                    page += 1
                else:
                    break
            except requests.RequestException as e:
                self.logger.error("Netwerkfout bij ophalen listings van NocoDB: %s", e)
                break
            except Exception as e:
                self.logger.error("Fout bij ophalen listings: %s", e)
                break
        self.logger.info("Gevonden %d bestaande listings", len(listings))
        return listings

    def get_table_schema(self) -> None:
        """Debug functie om tabelstructuur te tonen."""
        try:
            params = {"limit": 1}
            response = requests.get(self.api_endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            if data.get("list"):
                self.logger.info("Beschikbare velden: %s", list(data["list"][0].keys()))
            else:
                self.logger.info("Geen records gevonden in tabel")
        except Exception as e:
            self.logger.error("Fout bij ophalen tabelschema: %s", e)

    def parse_date(self, value: str) -> str:
        """Zet een datum string om naar het juiste formaat."""
        try:
            date_obj = datetime.strptime(value, '%d-%m-%Y')
            return date_obj.strftime('%Y-%m-%d')
        except ValueError as e:
            self.logger.error("Fout bij parsen van datum: %s", e)
            return value

    def _parse_markdown_data(self, markdown_data: str, listing_url: str) -> dict:
        """Parseert markdown data naar een dictionary voor NocoDB."""
        data = {
            "URL": listing_url,
            "Status": "Nieuw"
        }
        
        # Zet default datum voor Geplaatst
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        lines = markdown_data.split('\n')
        for line in lines:
            if line.startswith('- **'):
                key_value = line.replace('- **', '').split(':** ')
                if len(key_value) == 2:
                    key, value = key_value
                    if key in ['Functie', 'Klant', 'Branche', 'Regio']:
                        data[key] = value
                    elif key == 'Uren':
                        data[key] = value.replace("onbekend", "").strip()
                    elif key == 'Tarief':
                        data[key] = value
                    elif key in ['Geplaatst']:
                        parsed_date = self.parse_date(value)
                        if parsed_date:  # Alleen overschrijven als er een geldige datum is
                            data[key] = parsed_date
                        else:
                            data[key] = current_date
                    elif key in ['Sluiting']:
                        data[key] = self.parse_date(value)
        
        sections = markdown_data.split('## Functieomschrijving')
        if len(sections) > 1:
            data["Functieomschrijving"] = sections[-1].strip()
        
        return data

    def cleanup_closed_listings(self) -> int:
        """
        Verwijdert alle listings met status 'Closed' uit NocoDB.
        
        Returns:
            int: Aantal verwijderde records, -1 bij fouten
        """
        try:
            params = {
                "where": "(Status,eq,Closed)"
            }
            response = requests.get(self.api_endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            closed_records = data.get('list', [])
            
            if not closed_records:
                self.logger.info("Geen gesloten listings gevonden om op te schonen")
                return 0

            count = 0
            for record in closed_records:
                record_id = record.get("Id")
                if record_id:
                    delete_url = f"{self.api_endpoint}/{record_id}"
                    del_response = requests.delete(delete_url, headers=self.headers)
                    del_response.raise_for_status()
                    count += 1

            self.logger.info("Succesvol %d gesloten listings verwijderd", count)
            return count

        except requests.RequestException as e:
            self.logger.error("Netwerkfout bij opschonen listings: %s", str(e))
        except Exception as e:
            self.logger.error("Onverwachte fout bij opschonen listings: %s", str(e))
        return -1

    def get_lowest_listing_url(self) -> str:
        """Haalt de URL met de laagste waarde op uit de NocoDB tabel."""
        try:
            params = {"sort": "URL", "limit": 1}
            response = requests.get(self.api_endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            # Gebruik 'list' in plaats van 'data'
            records = data.get("list", [])
            if not records:
                self.logger.warning("Geen entries gevonden in de tabel")
                return "https://spinweb.nl/vacature/866905"  # Fallback URL
                
            lowest_url = records[0].get("URL", "")
            if not lowest_url:
                self.logger.warning("Geen URL gevonden in eerste record")
                return "https://spinweb.nl/vacature/866905"  # Fallback URL
                
            self.logger.info("Laagste URL gevonden: %s", lowest_url)
            return lowest_url
            
        except Exception as e:
            self.logger.error("Fout bij ophalen laagste URL: %s", str(e))
            return "https://spinweb.nl/aanvraag/866905"  # Fallback URL
            
    # Simple in-memory cache for listings
    _listings_cache = {
        "data": None,
        "timestamp": 0
    }
    
    def get_all_listings(self, force_refresh: bool = False) -> list:
        """
        Get all vacancy listings from NocoDB.
        
        Args:
            force_refresh (bool, optional): If True, bypass any caching and fetch fresh data. Defaults to False.
            
        Returns:
            List[Dict[str, Any]]: List of vacancy records
        """
        # Check cache first if not forcing refresh
        if not force_refresh:
            current_time = time.time()
            # Cache expires after 60 seconds
            if (self._listings_cache["data"] is not None and 
                current_time - self._listings_cache["timestamp"] < 60):
                self.logger.info(f"Returning {len(self._listings_cache['data'])} listings from cache")
                return self._listings_cache["data"]
        
        # First, try our already-verified API endpoint
        if not self.api_endpoint:
            self.logger.error("No valid API endpoint found for NocoDB")
            return []
            
        try:
            # Log the connection details (redacting sensitive info)
            self.logger.warning(f"Attempting to get listings from NocoDB at {self.api_endpoint}")
            token_info = "xc-token" if "xc-token" in self.headers else "xc-auth"
            self.logger.warning(f"Using headers with {token_info}")
            
            all_listings = []
            page = 1
            page_size = 1000  # Adjust as needed
            
            # Try different pagination parameters for different NocoDB versions
            pagination_params = [
                {"page": page, "pageSize": page_size},  # NocoDB v1
                {"offset": (page-1)*page_size, "limit": page_size},  # Alternative
                {"skip": (page-1)*page_size, "limit": page_size}  # Another alternative
            ]
            
            # First, try a simple request to determine which pagination format works
            pagination_format = None
            for params in pagination_params:
                try:
                    self.logger.warning(f"Testing pagination format with params: {params}")
                    response = requests.get(self.api_endpoint, headers=self.headers, params=params)
                    if response.ok:
                        self.logger.warning(f"Found working pagination format: {params}")
                        pagination_format = params
                        break
                except Exception:
                    pass
            
            if not pagination_format:
                self.logger.error("Could not determine pagination format")
                # Try a simple GET without pagination
                try:
                    response = requests.get(self.api_endpoint, headers=self.headers)
                    if response.ok:
                        self.logger.warning("Falling back to simple GET without pagination")
                        data = response.json()
                        
                        # Handle different response formats
                        if isinstance(data, list):
                            # Direct list of records
                            current_records = data
                        elif isinstance(data, dict):
                            # Try different known formats
                            if "list" in data:
                                current_records = data.get("list", [])
                            elif "data" in data:
                                current_records = data.get("data", [])
                            elif "records" in data:
                                current_records = data.get("records", [])
                            elif "rows" in data:
                                current_records = data.get("rows", [])
                            else:
                                # Last resort - try to find arrays in the response
                                arrays = [v for k, v in data.items() if isinstance(v, list) and len(v) > 0]
                                current_records = arrays[0] if arrays else []
                        else:
                            current_records = []
                        
                        # Add ID field to match the API format
                        for record in current_records:
                            # Try different field names for ID
                            if "Id" in record:
                                record["id"] = record.get("Id")
                            elif "id" not in record and "ID" in record:
                                record["id"] = record.get("ID")
                            elif "id" not in record:
                                # Generate an ID if none exists
                                import uuid
                                record["id"] = str(uuid.uuid4())
                        
                        all_listings = current_records
                        self.logger.warning(f"Retrieved {len(all_listings)} listings with simple GET")
                        return all_listings
                    else:
                        self.logger.error(f"Simple GET failed: {response.status_code} - {response.text}")
                except Exception as e:
                    self.logger.error(f"Error with simple GET: {str(e)}")
                return []
            
            # Use the determined pagination format
            while True:
                # Update page number in the pagination params
                if "page" in pagination_format:
                    params = {"page": page, "pageSize": pagination_format["pageSize"]}
                elif "offset" in pagination_format:
                    params = {"offset": (page-1)*pagination_format["limit"], "limit": pagination_format["limit"]}
                elif "skip" in pagination_format:
                    params = {"skip": (page-1)*pagination_format["limit"], "limit": pagination_format["limit"]}
                
                self.logger.info(f"Fetching page {page} with params: {params}")
                
                # Make the request
                try:
                    response = requests.get(self.api_endpoint, headers=self.headers, params=params)
                    self.logger.info(f"Request status code: {response.status_code}")
                    
                    # Log response headers
                    self.logger.info(f"Response headers: {dict(response.headers)}")
                    
                    # Log a small preview of the response body
                    try:
                        preview = str(response.text)[:200] + "..." if len(response.text) > 200 else response.text
                        self.logger.info(f"Response preview: {preview}")
                    except:
                        self.logger.info("Couldn't preview response")
                    
                    response.raise_for_status()
                except requests.RequestException as request_error:
                    self.logger.error(f"HTTP Request error: {str(request_error)}")
                    # Try to get response details if available
                    try:
                        if hasattr(request_error, 'response') and request_error.response is not None:
                            self.logger.error(f"Response status: {request_error.response.status_code}")
                            self.logger.error(f"Response body: {request_error.response.text}")
                    except:
                        pass
                    raise
                
                # Parse the response
                try:
                    data = response.json()
                    self.logger.info(f"Response parsed as JSON successfully")
                except json.JSONDecodeError as json_error:
                    self.logger.error(f"JSON parsing error: {str(json_error)}")
                    self.logger.error(f"Raw response: {response.text}")
                    raise
                
                # Log structure of response
                self.logger.info(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
                
                # Handle different response formats
                if isinstance(data, list):
                    current_records = data
                elif isinstance(data, dict):
                    if "list" in data:
                        current_records = data.get("list", [])
                    elif "data" in data:
                        current_records = data.get("data", [])
                    elif "records" in data:
                        current_records = data.get("records", [])
                    elif "rows" in data:
                        current_records = data.get("rows", [])
                    else:
                        # Last resort - try to find arrays in the response
                        arrays = [v for k, v in data.items() if isinstance(v, list) and len(v) > 0]
                        current_records = arrays[0] if arrays else []
                else:
                    current_records = []
                
                self.logger.info(f"Found {len(current_records)} records on page {page}")
                
                # No records? We're done
                if not current_records:
                    break
                
                # Add ID field to match the API format
                for record in current_records:
                    # Try different field names for ID
                    if "Id" in record:
                        record["id"] = record.get("Id")
                    elif "id" not in record and "ID" in record:
                        record["id"] = record.get("ID")
                    elif "id" not in record:
                        # Generate an ID if none exists
                        import uuid
                        record["id"] = str(uuid.uuid4())
                
                all_listings.extend(current_records)
                
                # Determine if we should continue pagination
                has_more = False
                
                # Check common pagination indicators
                if isinstance(data, dict):
                    page_info = data.get("pageInfo", {})
                    if page_info:
                        if "isLastPage" in page_info:
                            has_more = not page_info.get("isLastPage", True)
                        elif "hasNextPage" in page_info:
                            has_more = page_info.get("hasNextPage", False)
                    # Alternative pagination indicators
                    elif "hasNextPage" in data:
                        has_more = data.get("hasNextPage", False)
                    elif "next" in data and data.get("next") is not None:
                        has_more = True
                
                # If we didn't find pagination info, check if we got a full page of results
                if not has_more and len(current_records) >= pagination_format.get("pageSize", pagination_format.get("limit", 0)):
                    has_more = True
                
                if has_more:
                    page += 1
                else:
                    break
                
            self.logger.warning(f"Successfully retrieved {len(all_listings)} listings from NocoDB")
            
            # Update the cache
            self._listings_cache["data"] = all_listings
            self._listings_cache["timestamp"] = time.time()
            
            return all_listings
            
        except Exception as e:
            self.logger.error(f"Error getting all listings: {str(e)}", exc_info=True)
            
            # Last resort: try all possible URL combinations with GET
            self.logger.warning("Trying alternative methods as last resort...")
            for api_url in self.api_urls:
                try:
                    self.logger.warning(f"Trying simple GET with URL: {api_url}")
                    response = requests.get(api_url, headers=self.headers)
                    if response.ok:
                        data = response.json()
                        if isinstance(data, list) and len(data) > 0:
                            self.logger.warning(f"Found {len(data)} records with URL: {api_url}")
                            return data
                        elif isinstance(data, dict):
                            for key, value in data.items():
                                if isinstance(value, list) and len(value) > 0:
                                    self.logger.warning(f"Found {len(value)} records in key '{key}' with URL: {api_url}")
                                    return value
                except Exception:
                    continue
                
                # Try with alternative headers
                try:
                    self.logger.warning(f"Trying simple GET with URL: {api_url} and alternative headers")
                    response = requests.get(api_url, headers=NOCODB_HEADERS_ALT)
                    if response.ok:
                        data = response.json()
                        if isinstance(data, list) and len(data) > 0:
                            self.logger.warning(f"Found {len(data)} records with URL: {api_url} and alternative headers")
                            return data
                        elif isinstance(data, dict):
                            for key, value in data.items():
                                if isinstance(value, list) and len(value) > 0:
                                    self.logger.warning(f"Found {len(value)} records in key '{key}' with URL: {api_url} and alternative headers")
                                    return value
                except Exception:
                    continue
            
            return []