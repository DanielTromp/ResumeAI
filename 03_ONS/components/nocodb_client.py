import json
import datetime
import logging
import requests
from config import NOCODB_TOKEN, NOCODB_URL, NOCODB_PROJECT, NOCODB_TABLE

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
        self.api_endpoint = NOCODB_API_URL
        self.headers = NOCODB_HEADERS
        # Test de connectie
        try:
            response = requests.get(self.api_endpoint, headers=self.headers)
            response.raise_for_status()
            print("✅ NocoDB connection successful")
        except Exception as e:
            print(f"❌ NocoDB connection failed: {e}")
            print(f"API URL: {self.api_endpoint}")
            print(f"Headers: {self.headers}")
            raise

    def sanitize_url(self, url: str) -> str:
        """Maakt een URL veilig voor gebruik in NocoDB formules."""
        return url.replace("'", "\\'")

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
            date_obj = datetime.datetime.strptime(value, '%d-%m-%Y')
            return date_obj.strftime('%Y-%m-%d')
        except ValueError as e:
            self.logger.error("Fout bij parsen van datum: %s", e)
            return value

    def add_to_nocodb(self, markdown_data: str, listing_url: str) -> bool:
        """
        Voegt een nieuwe aanvraag toe aan de NocoDB tabel.
        
        Returns:
            bool: True als succesvol, False bij fouten
        """
        try:
            data = self._parse_markdown_data(markdown_data, listing_url)
            safe_url = self.sanitize_url(listing_url)
            # Bouw de filter als een string; URL-waarden moeten in quotes
            params = {"where": f"(URL,eq,'{safe_url}')"}
            response = requests.get(self.api_endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            # Gebruik de sleutel 'list' en haal de record-ID op met "Id"
            records = response.json().get("list", [])
            
            if records:
                record_id = records[0].get("Id")
                update_url = f"{self.api_endpoint}/{record_id}"
                response = requests.put(update_url, headers=self.headers, json=data)
                response.raise_for_status()
                self.logger.info("Aanvraag succesvol bijgewerkt: %s", listing_url)
            else:
                response = requests.post(self.api_endpoint, headers=self.headers, json=data)
                response.raise_for_status()
                self.logger.info("Nieuwe aanvraag toegevoegd: %s", listing_url)
            return True
            
        except requests.RequestException as e:
            self.logger.error("Netwerkfout bij toevoegen aan NocoDB: %s - %s", listing_url, str(e))
        except ValueError as e:
            self.logger.error("Ongeldige data voor NocoDB: %s - %s", listing_url, str(e))
        except KeyError as e:
            self.logger.error("Ontbrekend verplicht veld: %s - %s", listing_url, str(e))
        except (TypeError, AttributeError) as e:
            self.logger.error("Data structuur fout: %s - %s", listing_url, str(e))
        except Exception as e:
            self.logger.error("Onverwachte fout bij toevoegen aan NocoDB: %s - %s", listing_url, str(e))
        return False

    def _parse_markdown_data(self, markdown_data: str, listing_url: str) -> dict:
        """Parseert markdown data naar een dictionary voor NocoDB."""
        data = {
            "URL": listing_url,
            "Status": "Nieuw"
        }
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
                    elif key in ['Geplaatst', 'Sluiting']:
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