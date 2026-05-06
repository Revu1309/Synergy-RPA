"""
Real-time data synchronization utilities for live dashboard updates.
Provides thread-safe data caching and change detection for efficient updates.
"""

import threading
import json
from datetime import datetime, timezone
from typing import Dict, List, Callable, Any, Optional
from collections import defaultdict
import hashlib
import logging

logger = logging.getLogger(__name__)


class RealtimeDataCache:
    """Thread-safe cache for real-time data with change detection."""
    
    def __init__(self):
        self.lock = threading.RLock()
        self.data = {
            'crypto': {},
            'weather': {},
            'social_trends': {},
            'signal_fusion': None,
            'job_status': {},
        }
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.hashes: Dict[str, str] = defaultdict(str)
        self.last_update: Dict[str, datetime] = defaultdict(lambda: datetime.now(timezone.utc))
    
    def _compute_hash(self, data: Any) -> str:
        """Compute hash of data for change detection."""
        try:
            json_str = json.dumps(data, sort_keys=True, default=str)
            return hashlib.md5(json_str.encode()).hexdigest()
        except Exception as e:
            logger.warning(f"Failed to compute hash: {e}")
            return ""
    
    def update_crypto(self, crypto_data: List[Dict]) -> bool:
        """
        Update crypto data and notify subscribers if changed.
        
        Args:
            crypto_data: List of crypto asset dicts with symbol, name, price_usd, etc.
            
        Returns:
            True if data changed, False otherwise
        """
        with self.lock:
            new_hash = self._compute_hash(crypto_data)
            old_hash = self.hashes.get('crypto', '')
            
            if new_hash != old_hash:
                self.data['crypto'] = {item['symbol']: item for item in crypto_data}
                self.hashes['crypto'] = new_hash
                self.last_update['crypto'] = datetime.now(timezone.utc)
                self._notify_subscribers('crypto')
                return True
            return False
    
    def update_weather(self, weather_data: Dict) -> bool:
        """
        Update weather data and notify subscribers if changed.
        
        Args:
            weather_data: Dict with location names as keys and weather data as values
            
        Returns:
            True if data changed, False otherwise
        """
        with self.lock:
            new_hash = self._compute_hash(weather_data)
            old_hash = self.hashes.get('weather', '')
            
            if new_hash != old_hash:
                self.data['weather'] = weather_data
                self.hashes['weather'] = new_hash
                self.last_update['weather'] = datetime.now(timezone.utc)
                self._notify_subscribers('weather')
                return True
            return False
    
    def update_social_trends(self, trends_data: List[Dict]) -> bool:
        """
        Update social trends and notify subscribers if changed.
        
        Args:
            trends_data: List of trend dicts
            
        Returns:
            True if data changed, False otherwise
        """
        with self.lock:
            new_hash = self._compute_hash(trends_data)
            old_hash = self.hashes.get('social_trends', '')
            
            if new_hash != old_hash:
                self.data['social_trends'] = trends_data
                self.hashes['social_trends'] = new_hash
                self.last_update['social_trends'] = datetime.now(timezone.utc)
                self._notify_subscribers('social_trends')
                return True
            return False
    
    def update_signal_fusion(self, fusion_data: Dict) -> bool:
        """
        Update signal fusion index and notify subscribers if changed.
        
        Args:
            fusion_data: Signal fusion dict with scores and confidence
            
        Returns:
            True if data changed, False otherwise
        """
        with self.lock:
            new_hash = self._compute_hash(fusion_data)
            old_hash = self.hashes.get('signal_fusion', '')
            
            if new_hash != old_hash:
                self.data['signal_fusion'] = fusion_data
                self.hashes['signal_fusion'] = new_hash
                self.last_update['signal_fusion'] = datetime.now(timezone.utc)
                self._notify_subscribers('signal_fusion')
                return True
            return False
    
    def update_job_status(self, job_id: str, status: Dict) -> bool:
        """
        Update job status and notify subscribers if changed.
        
        Args:
            job_id: Unique job identifier
            status: Status dict with state, progress, etc.
            
        Returns:
            True if data changed, False otherwise
        """
        with self.lock:
            new_hash = self._compute_hash(status)
            old_hash = self.hashes.get(f'job_status_{job_id}', '')
            
            if new_hash != old_hash:
                self.data['job_status'][job_id] = status
                self.hashes[f'job_status_{job_id}'] = new_hash
                self.last_update['job_status'] = datetime.now(timezone.utc)
                self._notify_subscribers('job_status')
                return True
            return False
    
    def get_crypto(self, symbol: Optional[str] = None) -> Any:
        """Get crypto data for a specific symbol or all cryptos."""
        with self.lock:
            if symbol:
                return self.data['crypto'].get(symbol)
            return list(self.data['crypto'].values())
    
    def get_weather(self, location: Optional[str] = None) -> Any:
        """Get weather data for a specific location or all locations."""
        with self.lock:
            if location:
                return self.data['weather'].get(location)
            return self.data['weather']
    
    def get_social_trends(self) -> List[Dict]:
        """Get all social trends."""
        with self.lock:
            return self.data['social_trends']
    
    def get_signal_fusion(self) -> Optional[Dict]:
        """Get latest signal fusion index."""
        with self.lock:
            return self.data['signal_fusion']
    
    def get_job_status(self, job_id: Optional[str] = None) -> Any:
        """Get job status for a specific job or all jobs."""
        with self.lock:
            if job_id:
                return self.data['job_status'].get(job_id)
            return self.data['job_status']
    
    def subscribe(self, data_type: str, callback: Callable) -> None:
        """
        Subscribe to changes in a data type.
        
        Args:
            data_type: One of 'crypto', 'weather', 'social_trends', 'signal_fusion', 'job_status'
            callback: Function to call when data changes, receives data dict
        """
        with self.lock:
            self.subscribers[data_type].append(callback)
    
    def unsubscribe(self, data_type: str, callback: Callable) -> None:
        """Unsubscribe from a data type."""
        with self.lock:
            if callback in self.subscribers[data_type]:
                self.subscribers[data_type].remove(callback)
    
    def _notify_subscribers(self, data_type: str) -> None:
        """Notify all subscribers of a data type change (call within lock)."""
        try:
            callbacks = self.subscribers.get(data_type, [])[:]  # Copy to avoid mutation during iteration
            data = self.data.get(data_type)
            for callback in callbacks:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in subscriber callback for {data_type}: {e}")
        except Exception as e:
            logger.error(f"Error notifying subscribers for {data_type}: {e}")
    
    def get_all_stats(self) -> Dict:
        """Get cache statistics for monitoring."""
        with self.lock:
            return {
                'crypto_count': len(self.data['crypto']),
                'weather_locations': len(self.data['weather']),
                'social_trends_count': len(self.data['social_trends']),
                'job_count': len(self.data['job_status']),
                'last_updates': {
                    k: v.isoformat() if isinstance(v, datetime) else str(v)
                    for k, v in self.last_update.items()
                }
            }


# Global cache instance
_cache_instance: Optional[RealtimeDataCache] = None
_cache_lock = threading.Lock()


def _seed_mock_realtime_data(cache: RealtimeDataCache) -> None:
    """Seed the realtime cache with mock data so the dashboard isn't empty
    before the scheduler has run (useful for local dev / missing API keys).

    This function is intentionally safe to call multiple times.
    """
    now = datetime.now(timezone.utc).isoformat()

    # Crypto: few representative assets
    crypto_seed = [
        {
            'symbol': 'BTC',
            'name': 'Bitcoin',
            'price_usd': 65000.0,
            'market_cap': 1_200_000_000_000,
            'volume_24h': 35_000_000_000,
            'timestamp': now,
        },
        {
            'symbol': 'ETH',
            'name': 'Ethereum',
            'price_usd': 3200.0,
            'market_cap': 380_000_000_000,
            'volume_24h': 18_000_000_000,
            'timestamp': now,
        },
        {
            'symbol': 'SOL',
            'name': 'Solana',
            'price_usd': 150.0,
            'market_cap': 70_000_000_00,
            'volume_24h': 3_500_000_000,
            'timestamp': now,
        },
    ]

    # Weather: two locations
    weather_seed = {
        'New York, US': {
            'location_name': 'New York, US',
            'latitude': 40.7128,
            'longitude': -74.0060,
            'temperature': 22.5,
            'humidity': 65.0,
            'wind_speed': 3.2,
            'weather_main': 'Clear',
            'timestamp': now,
        },
        'London, UK': {
            'location_name': 'London, UK',
            'latitude': 51.5072,
            'longitude': -0.1276,
            'temperature': 16.8,
            'humidity': 72.0,
            'wind_speed': 4.1,
            'weather_main': 'Clouds',
            'timestamp': now,
        },
    }

    # Social trends: representative entries
    social_seed = [
        {
            'name': '#Bitcoin',
            'source': 'twitter',
            'tweet_volume': 50000,
            'sentiment': 0.42,
            'timestamp': now,
        },
        {
            'name': '#Ethereum',
            'source': 'twitter',
            'tweet_volume': 32000,
            'sentiment': 0.35,
            'timestamp': now,
        },
        {
            'name': '#Weather',
            'source': 'twitter',
            'tweet_volume': 12000,
            'sentiment': 0.10,
            'timestamp': now,
        },
    ]

    # Signal fusion: simple normalized structure
    fusion_seed = {
        'fusion_score': 0.71,
        'crypto_score': 0.62,
        'social_score': 0.74,
        'weather_score': 0.80,
        'confidence_level': 'medium',
        'timestamp': now,
    }

    # Job status placeholder
    job_seed = {
        'state': 'idle',
        'progress': 0,
        'last_update': now,
    }

    with cache.lock:
        # Only seed if the cache is empty-ish
        if len(cache.data.get('crypto', {})) == 0 and len(cache.data.get('weather', {})) == 0 and len(cache.data.get('social_trends', [])) == 0:
            cache.update_crypto(crypto_seed)
            cache.update_weather(weather_seed)
            cache.update_social_trends(social_seed)
            cache.update_signal_fusion(fusion_seed)
            cache.update_job_status('seed', job_seed)


def get_realtime_cache() -> RealtimeDataCache:
    """Get or create the global realtime data cache instance.

    Additionally seeds mock data on first creation so the frontend can render
    immediately in dev/testing environments where scrapers may not have run yet.
    """
    global _cache_instance
    if _cache_instance is None:
        with _cache_lock:
            if _cache_instance is None:
                _cache_instance = RealtimeDataCache()
                _seed_mock_realtime_data(_cache_instance)
    return _cache_instance

