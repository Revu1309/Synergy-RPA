"""Weather data scraper using OpenWeatherMap API."""

import requests
import os
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

# Fallback locations (used if database is unavailable)
FALLBACK_LOCATIONS = [
    {"name": "New York", "lat": 40.7128, "lon": -74.0060, "country": "USA"},
    {"name": "London", "lat": 51.5074, "lon": -0.1278, "country": "UK"},
    {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503, "country": "Japan"},
    {"name": "Dubai", "lat": 25.2048, "lon": 55.2708, "country": "UAE"},
    {"name": "Sydney", "lat": -33.8688, "lon": 151.2093, "country": "Australia"},
    {"name": "Delhi", "lat": 28.7041, "lon": 77.1025, "country": "India"},
    {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "country": "India"},
    {"name": "Bangalore", "lat": 12.9716, "lon": 77.5946, "country": "India"},
    {"name": "Chennai", "lat": 13.0827, "lon": 80.2707, "country": "India"},
    {"name": "Kolkata", "lat": 22.5726, "lon": 88.3639, "country": "India"},
]

def get_predefined_locations() -> List[Dict]:
    """Get predefined cities from database."""
    try:
        from database.predefined_cities import PredefinedCitiesManager
        cities = PredefinedCitiesManager.get_all_cities(active_only=True)
        
        if cities:
            # Convert database format to scraper format
            locations = []
            for city in cities:
                locations.append({
                    'name': city['city_name'],
                    'lat': city['latitude'],
                    'lon': city['longitude'],
                    'country': city['country']
                })
            return locations
    except Exception as e:
        print(f"Error fetching cities from database: {e}")
    
    # Fallback to hardcoded locations if database fails
    return FALLBACK_LOCATIONS

def get_weather_data(locations: List[Dict] = None) -> List[Dict]:
    """
    Fetch weather data for locations.
    
    Args:
        locations: List of location dicts with 'location_name' or 'name', 'latitude' or 'lat', 
                  'longitude' or 'lon', and optionally 'country'
                  If None, fetches from database predefined cities
    
    Returns:
        List of weather data dicts
    """
    if locations is None:
        locations = get_predefined_locations()
    
    api_key = os.getenv('OPENWEATHER_API_KEY', 'demo_key')
    
    # If API key is not configured, return empty data
    if api_key == 'demo_key':
        return []
    
    weather_data = []
    
    for location in locations:
        try:
            # Support both naming conventions
            name = location.get('location_name') or location.get('name')
            lat = location.get('latitude') or location.get('lat')
            lon = location.get('longitude') or location.get('lon')
            country = location.get('country', '')
            
            # Using OpenWeatherMap Current Weather API
            url = 'https://api.openweathermap.org/data/2.5/weather'
            params = {
                'lat': lat,
                'lon': lon,
                'appid': api_key,
                'units': 'metric'  # Use Celsius
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            weather_entry = {
                'location_name': name,
                'country': country,
                'latitude': lat,
                'longitude': lon,
                'temperature': data.get('main', {}).get('temp'),
                'feels_like': data.get('main', {}).get('feels_like'),
                'humidity': data.get('main', {}).get('humidity'),
                'pressure': data.get('main', {}).get('pressure'),
                'wind_speed': data.get('wind', {}).get('speed'),
                'wind_direction': data.get('wind', {}).get('deg'),
                'cloudiness': data.get('clouds', {}).get('all'),
                'weather_main': data.get('weather', [{}])[0].get('main'),
                'weather_description': data.get('weather', [{}])[0].get('description'),
                'visibility': data.get('visibility'),
                'rainfall': data.get('rain', {}).get('1h', 0),
                'snow': data.get('snow', {}).get('1h', 0),
                'uv_index': None  # Can be added with a separate call
            }
            
            weather_data.append(weather_entry)
            
        except requests.RequestException as e:
            print(f"Error fetching weather for {location.get('name', 'Unknown')}: {e}")
            # Return empty/default data for this location
            name = location.get('location_name') or location.get('name')
            lat = location.get('latitude') or location.get('lat')
            lon = location.get('longitude') or location.get('lon')
            country = location.get('country', '')
            
            weather_entry = {
                'location_name': name,
                'country': country,
                'latitude': lat,
                'longitude': lon,
                'temperature': None,
                'error': str(e)
            }
            weather_data.append(weather_entry)
    
    return weather_data


def get_weather_forecast(lat: float, lon: float, api_key: str = None) -> Dict:
    """
    Get weather forecast for a specific location.
    
    Args:
        lat: Latitude
        lon: Longitude
        api_key: OpenWeatherMap API key (uses env if not provided)
    
    Returns:
        Forecast data dictionary
    """
    if api_key is None:
        api_key = os.getenv('OPENWEATHER_API_KEY', 'demo_key')
    
    # If API key is not configured, return empty data
    if api_key == 'demo_key':
        return {}
    
    try:
        url = 'https://api.openweathermap.org/data/2.5/forecast'
        params = {
            'lat': lat,
            'lon': lon,
            'appid': api_key,
            'units': 'metric'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        return response.json()
    
    except requests.RequestException as e:
        print(f"Error fetching forecast: {e}")
        return {}
