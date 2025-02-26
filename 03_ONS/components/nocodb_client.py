"""
NocoDB client

Author: Daniel Tromp
Email: drpgmtromp@gmail.com
Version: 0.0.1
Created: 2025-02-24
Updated: 2025-02-24
License: MIT
Repository: https://github.com/DanielTromp/ResumeAI
"""

import json
import datetime
import logging
import requests
from config import NOCODB_TOKEN, NOCODB_URL, NOCODB_PROJECT, NOCODB_TABLE
from datetime import datetime

# Constants voor NocoDB
NOCODB_API_URL = f"{NOCODB_URL}/api/v1/db/data/v1/{NOCODB_PROJECT}/{NOCODB_TABLE}"
NOCODB_HEADERS = {
    "accept": "application/json",
    "Content-Type": "application/json",
    "xc-token": NOCODB_TOKEN
}

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

        self.api_endpoint = NOCODB_API_URL
        self.headers = NOCODB_HEADERS
        try:
            response = requests.get(self.api_endpoint, headers=self.headers)
            response.raise_for_status()
            self.logger.info("✅ NocoDB connection successful")
        except Exception as e:
            self.logger.error(f"❌ NocoDB connection failed: {e}")
            self.logger.error(f"API URL: {self.api_endpoint}")
            self.logger.error(f"Headers: {self.headers}")
            raise

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
            
            # Normaliseer de URL voor zowel de zoekopdracht als de data
            normalized_url = self.normalize_url(listing_url)
            
            # Zoek naar het record met de genormaliseerde URL (zonder quotes voor betere vergelijking)
            params = {"where": f"(URL,eq,{normalized_url})"}
            self.logger.info("Zoeken naar record met genormaliseerde URL: %s", normalized_url)
            self.logger.info("Zoekquery parameters: %s", params)
            
            response = requests.get(self.api_endpoint, headers=self.headers, params=params)
            
            # Als de query mislukt, probeer dan met quotes eromheen
            if not response.ok:
                params = {"where": f"(URL,eq,'{normalized_url}')"}
                self.logger.info("Eerste query mislukt, proberen met quotes: %s", params)
                response = requests.get(self.api_endpoint, headers=self.headers, params=params)
            
            response.raise_for_status()
            
            # Log de volledige response voor debugging
            self.logger.debug("Zoekresultaat response:")
            self.logger.debug(json.dumps(response.json(), indent=2))
            
            records = response.json().get("list", [])
            
            self.logger.info("Aantal gevonden records: %d", len(records))
            if records:
                self.logger.info("Gevonden record details: %s", json.dumps(records[0], indent=2))
            
            if records:
                # Update bestaand record
                record_id = records[0].get("Id")
                update_url = f"{self.api_endpoint}/{record_id}"
                
                # Gebruik de genormaliseerde URL in de data
                data["URL"] = normalized_url
                
                self.logger.info("Update URL: %s", update_url)
                self.logger.info("Update data: %s", json.dumps(data, indent=2))
                
                try:
                    response = requests.put(update_url, headers=self.headers, json=data)
                    response.raise_for_status()
                    
                    # Log de update response
                    self.logger.debug("Update response:")
                    self.logger.debug(json.dumps(response.json(), indent=2))
                    
                    self.logger.info("Record succesvol bijgewerkt: %s (ID: %s)", normalized_url, record_id)
                    return True
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 404:
                        # Record niet gevonden (mogelijk verwijderd), probeer het toe te voegen als nieuw record
                        self.logger.warning("Record met ID %s niet gevonden (404), voeg toe als nieuw record", record_id)
                        response = requests.post(self.api_endpoint, headers=self.headers, json=data)
                        response.raise_for_status()
                        
                        # Log de create response
                        self.logger.debug("Create response (na 404):")
                        response_data = response.json()
                        self.logger.debug(json.dumps(response_data, indent=2))
                        
                        new_id = response_data.get("id")
                        self.logger.info("Nieuw record toegevoegd na 404: %s (ID: %s)", normalized_url, new_id)
                        return True
                    else:
                        # Andere HTTP fouten opnieuw werpen
                        raise
            else:
                # Voeg nieuw record toe met genormaliseerde URL
                data["URL"] = normalized_url
                self.logger.info("Nieuwe data voor toevoegen: %s", json.dumps(data, indent=2))
                
                response = requests.post(self.api_endpoint, headers=self.headers, json=data)
                response.raise_for_status()
                
                # Log de create response
                self.logger.debug("Create response:")
                response_data = response.json()
                self.logger.debug(json.dumps(response_data, indent=2))
                
                new_id = response_data.get("id")
                self.logger.info("Nieuw record toegevoegd: %s (ID: %s)", normalized_url, new_id)
                return True
        except Exception as e:
            self.logger.error("Fout bij updaten record: %s - %s", listing_url, str(e))
            self.logger.error("API endpoint: %s", self.api_endpoint)
            self.logger.error("Headers: %s", self.headers)
            self.logger.exception("Stack trace:")
            
            # Laatste poging - probeer altijd een nieuw record toe te voegen bij fatale fouten
            try:
                self.logger.info("Laatste poging: toevoegen als nieuw record na fout")
                data["URL"] = self.normalize_url(listing_url)
                response = requests.post(self.api_endpoint, headers=self.headers, json=data)
                response.raise_for_status()
                new_id = response.json().get("id")
                self.logger.info("Nieuw record succesvol toegevoegd na fout: %s (ID: %s)", data["URL"], new_id)
                return True
            except Exception as inner_e:
                self.logger.error("Ook laatste poging om record toe te voegen mislukt: %s", str(inner_e))
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
            print(lowest_url)
            if not lowest_url:
                self.logger.warning("Geen URL gevonden in eerste record")
                return "https://spinweb.nl/vacature/866905"  # Fallback URL
                
            self.logger.info("Laagste URL gevonden: %s", lowest_url)
            return lowest_url
            
        except Exception as e:
            self.logger.error("Fout bij ophalen laagste URL: %s", str(e))
            return "https://spinweb.nl/aanvraag/866905"  # Fallback URL

