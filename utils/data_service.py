"""
Unified data service for consistent real-time data handling.
Standardizes data formats across all sources (crypto, weather, social).
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)


class DataValidationError(Exception):
    """Raised when data validation fails."""
    pass


class CryptoDataService:
    """Standardized crypto data handling."""
    
    @staticmethod
    def normalize_crypto_entry(data: Dict) -> Dict:
        """
        Normalize a crypto asset entry to standard format.
        
        Expected input fields (flexible naming):
            - symbol (or ticker)
            - name
            - price_usd (or price)
            - market_cap (optional)
            - volume_24h (or volume)
            - timestamp (or created_at) - optional, defaults to now
            
        Returns:
            Normalized dict with guaranteed fields
        """
        try:
            timestamp = data.get('timestamp') or data.get('created_at') or datetime.now(timezone.utc)
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            elif not isinstance(timestamp, datetime):
                timestamp = datetime.now(timezone.utc)
            
            normalized = {
                'symbol': (data.get('symbol') or data.get('ticker') or '').upper(),
                'name': data.get('name') or '',
                'price_usd': float(data.get('price_usd') or data.get('price') or 0),
                'market_cap': float(data.get('market_cap') or 0) if data.get('market_cap') else None,
                'volume_24h': float(data.get('volume_24h') or data.get('volume') or 0),
                'timestamp': timestamp.isoformat(),
                'source': data.get('source', 'unknown'),
                'metadata': data.get('metadata', {}),
            }
            
            # Validate critical fields
            if not normalized['symbol']:
                raise DataValidationError("Missing symbol")
            if normalized['price_usd'] < 0:
                raise DataValidationError("Price cannot be negative")
            
            return normalized
        except (KeyError, ValueError, TypeError) as e:
            raise DataValidationError(f"Failed to normalize crypto entry: {e}")
    
    @staticmethod
    def normalize_crypto_list(data_list: List[Dict]) -> List[Dict]:
        """Normalize a list of crypto entries."""
        normalized = []
        for item in data_list:
            try:
                normalized.append(CryptoDataService.normalize_crypto_entry(item))
            except DataValidationError as e:
                logger.warning(f"Skipping invalid crypto entry: {e}")
        return normalized


class WeatherDataService:
    """Standardized weather data handling."""
    
    @staticmethod
    def normalize_weather_entry(data: Dict) -> Dict:
        """
        Normalize a weather entry to standard format.
        
        Expected input fields (flexible naming):
            - location_name (or location, city, name)
            - latitude (or lat)
            - longitude (or lon)
            - country (optional)
            - temperature (required, in Celsius)
            - feels_like (optional)
            - humidity (optional, 0-100)
            - pressure (optional, hPa)
            - wind_speed (optional, m/s)
            - wind_direction (optional, degrees)
            - weather_main (optional, e.g., "Clouds", "Rain")
            - weather_description (optional)
            - cloudiness (optional, 0-100)
            - visibility (optional, meters)
            - rainfall (optional, mm)
            - timestamp (optional, defaults to now)
            
        Returns:
            Normalized dict with guaranteed fields
        """
        try:
            timestamp = data.get('timestamp') or data.get('created_at') or datetime.now(timezone.utc)
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            elif not isinstance(timestamp, datetime):
                timestamp = datetime.now(timezone.utc)
            
            location_name = (
                data.get('location_name') or 
                data.get('location') or 
                data.get('city') or 
                data.get('name') or 
                'Unknown'
            )
            
            temperature = float(data.get('temperature') or 0)
            
            normalized = {
                'location_name': location_name,
                'latitude': float(data.get('latitude') or data.get('lat') or 0),
                'longitude': float(data.get('longitude') or data.get('lon') or 0),
                'country': data.get('country', ''),
                'temperature': temperature,
                'feels_like': float(data.get('feels_like') or temperature),
                'humidity': float(data.get('humidity') or 0),
                'pressure': float(data.get('pressure') or 0),
                'wind_speed': float(data.get('wind_speed') or 0),
                'wind_direction': float(data.get('wind_direction') or 0),
                'weather_main': data.get('weather_main') or '',
                'weather_description': data.get('weather_description') or '',
                'cloudiness': float(data.get('cloudiness') or 0),
                'visibility': float(data.get('visibility') or 0),
                'rainfall': float(data.get('rainfall') or 0),
                'timestamp': timestamp.isoformat(),
                'metadata': data.get('metadata', {}),
            }
            
            # Validate critical fields
            if not normalized['location_name'] or normalized['location_name'] == 'Unknown':
                if normalized['latitude'] == 0 and normalized['longitude'] == 0:
                    raise DataValidationError("Missing location information")
            
            return normalized
        except (KeyError, ValueError, TypeError) as e:
            raise DataValidationError(f"Failed to normalize weather entry: {e}")
    
    @staticmethod
    def normalize_weather_list(data_list: List[Dict]) -> List[Dict]:
        """Normalize a list of weather entries."""
        normalized = []
        for item in data_list:
            try:
                normalized.append(WeatherDataService.normalize_weather_entry(item))
            except DataValidationError as e:
                logger.warning(f"Skipping invalid weather entry: {e}")
        return normalized


class SocialTrendDataService:
    """Standardized social trend data handling."""
    
    @staticmethod
    def normalize_trend_entry(data: Dict) -> Dict:
        """
        Normalize a social trend entry to standard format.
        
        Expected input fields (flexible naming):
            - name (required)
            - rank (optional, int)
            - url (optional)
            - tweet_volume (optional)
            - source (required, e.g., 'twitter', 'reddit')
            - sentiment (optional, -1 to 1)
            - volume (optional, int)
            - timestamp (optional, defaults to now)
            
        Returns:
            Normalized dict with guaranteed fields
        """
        try:
            timestamp = data.get('timestamp') or data.get('created_at') or datetime.now(timezone.utc)
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            elif not isinstance(timestamp, datetime):
                timestamp = datetime.now(timezone.utc)
            
            source = (data.get('source') or '').lower()
            
            normalized = {
                'name': data.get('name') or '',
                'rank': int(data.get('rank') or 0),
                'url': data.get('url') or '',
                'source': source,
                'tweet_volume': int(data.get('tweet_volume') or data.get('volume') or 0),
                'sentiment': float(data.get('sentiment') or 0),
                'timestamp': timestamp.isoformat(),
                'metadata': data.get('metadata', {}),
            }
            
            # Validate critical fields
            if not normalized['name']:
                raise DataValidationError("Missing trend name")
            if not normalized['source']:
                raise DataValidationError("Missing trend source")
            
            # Clamp sentiment to valid range
            normalized['sentiment'] = max(-1.0, min(1.0, normalized['sentiment']))
            
            return normalized
        except (KeyError, ValueError, TypeError) as e:
            raise DataValidationError(f"Failed to normalize trend entry: {e}")
    
    @staticmethod
    def normalize_trend_list(data_list: List[Dict]) -> List[Dict]:
        """Normalize a list of trend entries."""
        normalized = []
        for item in data_list:
            try:
                normalized.append(SocialTrendDataService.normalize_trend_entry(item))
            except DataValidationError as e:
                logger.warning(f"Skipping invalid trend entry: {e}")
        return normalized


class JobStatusService:
    """Standardized job status data handling."""
    
    @staticmethod
    def normalize_job_status(data: Dict) -> Dict:
        """
        Normalize a job status entry.
        
        Expected input fields:
            - job_id (required)
            - job_name (required)
            - state ('running', 'completed', 'failed', 'pending')
            - progress (0-100, optional)
            - started_at (optional)
            - completed_at (optional)
            - error_message (optional)
            
        Returns:
            Normalized dict with guaranteed fields
        """
        try:
            now = datetime.now(timezone.utc).isoformat()
            
            normalized = {
                'job_id': data.get('job_id') or '',
                'job_name': data.get('job_name') or '',
                'state': data.get('state', 'pending').lower(),
                'progress': int(data.get('progress') or 0),
                'started_at': data.get('started_at') or now,
                'completed_at': data.get('completed_at'),
                'error_message': data.get('error_message') or '',
                'metadata': data.get('metadata', {}),
            }
            
            # Validate critical fields
            if not normalized['job_id']:
                raise DataValidationError("Missing job_id")
            if normalized['state'] not in ('running', 'completed', 'failed', 'pending'):
                normalized['state'] = 'pending'
            normalized['progress'] = max(0, min(100, normalized['progress']))
            
            return normalized
        except (KeyError, ValueError, TypeError) as e:
            raise DataValidationError(f"Failed to normalize job status: {e}")
    
    @staticmethod
    def normalize_job_status_list(data_list: List[Dict]) -> List[Dict]:
        """Normalize a list of job statuses."""
        normalized = []
        for item in data_list:
            try:
                normalized.append(JobStatusService.normalize_job_status(item))
            except DataValidationError as e:
                logger.warning(f"Skipping invalid job status: {e}")
        return normalized


class DataService:
    """Main unified data service."""
    
    CRYPTO = CryptoDataService()
    WEATHER = WeatherDataService()
    SOCIAL_TRENDS = SocialTrendDataService()
    JOB_STATUS = JobStatusService()
    
    @staticmethod
    def get_formatted_response(success: bool, data: Any = None, message: str = '', error: str = '') -> Dict:
        """
        Format a standard API response.
        
        Args:
            success: Whether the operation was successful
            data: The data to return (can be None)
            message: Optional success message
            error: Optional error message
            
        Returns:
            Standard response dict
        """
        return {
            'success': success,
            'data': data,
            'message': message or ('Success' if success else 'Failed'),
            'error': error,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
