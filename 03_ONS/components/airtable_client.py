"""
AirtableClient module voor het beheren van Airtable CRUD operaties.
"""

import datetime
import logging
import requests
from pyairtable import Api
from config import *

class AirtableClient:
    """Centrale class voor Airtable interacties."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        try:
            self.api = Api(AIRTABLE_API_KEY)
            self.aanvragen_table = self.api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE1)
        except requests.RequestException as e:
            self.logger.error("Netwerkfout bij initialiseren Airtable API: %s", e)
            raise
        except ValueError as e:
            self.logger.error("Ongeldige API key of tabel configuratie: %s", e)
            raise
        except (KeyError, TypeError) as e:
            self.logger.error("Ongeldige configuratie parameters: %s", e)
            raise
        except AttributeError as e:
            self.logger.error("Ontbrekende verplichte Airtable configuratie: %s", e)
            raise

    def sanitize_url(self, url: str) -> str:
        """Maakt een URL veilig voor gebruik in Airtable formules."""
        return url.replace("'", "\\'")

    def get_existing_listings(self) -> set:
        """Haalt bestaande listings op uit Airtable."""
        try:
            records = self.aanvragen_table.all()
            listings = {record['fields']['URL']
                       for record in records
                       if 'URL' in record['fields']}
            self.logger.info("Gevonden %d bestaande listings", len(listings))
            return listings
        except requests.RequestException as e:
            self.logger.error("Netwerkfout bij ophalen listings van Airtable: %s", e)
            return set()
        except Exception as e:
            self.logger.error("Fout bij ophalen listings: %s", e)
            return set()

    def get_table_schema(self) -> None:
        """Debug functie om tabelstructuur te tonen."""
        try:
            record = self.aanvragen_table.first()
            if record:
                self.logger.info("Beschikbare velden: %s", list(record['fields'].keys()))
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

    def add_to_airtable(self, markdown_data: str, listing_url: str) -> bool:
        """
        Voegt een nieuwe aanvraag toe aan de Aanvragen tabel.
        
        Returns:
            bool: True als succesvol, False bij fouten
        """
        try:
            data = self._parse_markdown_data(markdown_data, listing_url)
            safe_url = self.sanitize_url(listing_url)
            existing_records = self.aanvragen_table.all(
                formula=f"FIND('{safe_url}', {{URL}})"
            )

            if existing_records:
                record_id = existing_records[0]['id']
                self.aanvragen_table.update(record_id, data)
                self.logger.info("Aanvraag succesvol bijgewerkt: %s", listing_url)
            else:
                self.aanvragen_table.create(data)
                self.logger.info("Nieuwe aanvraag toegevoegd: %s", listing_url)
            return True
            
        except requests.RequestException as e:
            self.logger.error("Netwerkfout bij toevoegen aan Airtable: %s - %s",
                            listing_url, str(e))
        except ValueError as e:
            self.logger.error("Ongeldige data voor Airtable: %s - %s",
                            listing_url, str(e))
        except KeyError as e:
            self.logger.error("Ontbrekend verplicht veld: %s - %s",
                            listing_url, str(e))
        except (TypeError, AttributeError) as e:
            self.logger.error("Data structuur fout: %s - %s",
                            listing_url, str(e))
        except Exception as e:
            self.logger.error("Onverwachte fout bij toevoegen aan Airtable: %s - %s",
                            listing_url, str(e))
        return False

    def _parse_markdown_data(self, markdown_data: str, listing_url: str) -> dict:
        """Parseert markdown data naar een dictionary voor Airtable."""
        data = {
            'URL': listing_url,
            'Status': 'Nieuw'
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
            data['Functieomschrijving'] = sections[-1].strip()

        return data

    def cleanup_closed_listings(self) -> int:
        """
        Verwijdert alle listings met status 'Closed' uit Airtable.
        
        Returns:
            int: Aantal verwijderde records, -1 bij fouten
        """
        try:
            closed_records = self.aanvragen_table.all(formula="Status='Closed'")
            if not closed_records:
                self.logger.info("Geen gesloten listings gevonden om op te schonen")
                return 0

            record_ids = [record['id'] for record in closed_records]
            self.aanvragen_table.batch_delete(record_ids)
            
            count = len(record_ids)
            self.logger.info(f"Succesvol {count} gesloten listings verwijderd")
            return count
            
        except requests.RequestException as e:
            self.logger.error("Netwerkfout bij opschonen listings: %s", str(e))
        except Exception as e:
            self.logger.error("Onverwachte fout bij opschonen listings: %s", str(e))
        return -1

    def get_lowest_listing_url(self) -> str:
        """Haalt de URL met de laagste waarde op uit de Aanvragen tabel."""
        try:
            records = self.aanvragen_table.all(sort=['URL'])
            
            if not records:
                self.logger.warning("Geen entries gevonden in Aanvragen tabel")
                return "https://spinweb.nl/vacature/864984"  # Fallback URL
                
            lowest_url = records[0]['fields'].get('URL', '')
            
            if not lowest_url:
                self.logger.warning("Geen URL gevonden in eerste record")
                return "https://spinweb.nl/vacature/864984"  # Fallback URL
                
            self.logger.info(f"Laagste URL gevonden: {lowest_url}")
            return lowest_url
            
        except Exception as e:
            self.logger.error(f"Fout bij ophalen laagste URL: {str(e)}")
            return "https://spinweb.nl/vacature/864984"  # Fallback URL 