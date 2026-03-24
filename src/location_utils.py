"""
location_utils.py
=================
Geocoding utilities for ROPIAS to resolve city names to coordinates.
"""
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

def get_coordinates_from_city(city_name: str) -> tuple:
    """
    Takes a city name (e.g., 'Nakuru') and returns (latitude, longitude, formatted_address).
    Bias is strongly set to Kenya.
    Returns (None, None, None) if not found or error.
    """
    if not city_name or not str(city_name).strip():
        return None, None, None
        
    geolocator = Nominatim(user_agent="ropias_agritech_app")
    try:
        # Append Kenya to strongly bias results
        query = f"{city_name.strip()}, Kenya"
        location = geolocator.geocode(query, timeout=10)
        if location:
            return location.latitude, location.longitude, location.address
        return None, None, None
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"Geocoding error: {e}")
        return None, None, None
