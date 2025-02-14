import os
from dotenv import load_dotenv
import openrouteservice
from geopy.geocoders import Nominatim

# Laad API-sleutel uit .env
load_dotenv()
OPENROUTESERVICE_KEY = os.getenv("OPENROUTESERVICE")

# Configuratie
RADIUS = 4000  # Maximale zoekradius voor routes

class RoutePlanner:
    def __init__(self, start_city, end_city, transport_mode="driving-car"):
        """Initialiseer de routeplanner met start- en eindstad."""
        self.client = openrouteservice.Client(key=OPENROUTESERVICE_KEY)
        self.geolocator = Nominatim(user_agent="geoapi")
        self.start_city = start_city
        self.end_city = end_city
        self.transport_mode = transport_mode

    def _get_coordinates(self, city):
        """Haalt de coördinaten van een stad op en valideert deze."""
        location = self.geolocator.geocode(city + ", Nederland")
        if location:
            coords = [location.longitude, location.latitude]
            print(f"Coördinaten voor {city}: {coords}")  # Debugging

            if self._is_valid_location(coords):
                return coords
            else:
                print(f"Geen routable locatie gevonden voor {city}, probeer een nabijgelegen stad.")
        else:
            print(f"Kon geen coördinaten vinden voor {city}.")
        return None

    def _is_valid_location(self, coords):
        """Checkt of de coördinaten routable zijn door een testroute te maken."""
        try:
            self.client.directions(
                coordinates=[coords, coords],
                profile=self.transport_mode,
                format="geojson",
                radiuses=[RADIUS, RADIUS]
            )
            return True
        except openrouteservice.exceptions.ApiError:
            return False

    def calculate_route(self):
        """Bereken de reisafstand en tijd tussen start- en eindstad."""
        start_coords = self._get_coordinates(self.start_city)
        end_coords = self._get_coordinates(self.end_city)

        if not start_coords or not end_coords:
            return "Kon de reistijd niet berekenen."

        try:
            route = self.client.directions(
                coordinates=[start_coords, end_coords],
                profile=self.transport_mode,
                format='geojson',
                radiuses=[RADIUS, RADIUS]
            )

            distance_km = round(route['features'][0]['properties']['segments'][0]['distance'] / 1000)
            duration_min = round(route['features'][0]['properties']['segments'][0]['duration'] / 60)

            return {self.start_city}, {self.end_city}, {distance_km}, {duration_min}

        except openrouteservice.exceptions.ApiError as e:
            return f"Kan geen route berekenen tussen {self.start_city} en {self.end_city}. Fout: {e}"

# ✅ Voorbeeldgebruik:
#route = RoutePlanner("Almere", "Den Helder")
print(RoutePlanner("Almere", "Den Helder").calculate_route())
