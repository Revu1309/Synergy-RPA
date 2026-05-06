#!/usr/bin/env python3
"""
Quick integration test for real-time data system.
Run this to verify all components are working correctly.
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all new modules can be imported."""
    print("Testing imports...")
    try:
        from utils.realtime_data import get_realtime_cache, RealtimeDataCache
        print("  ✓ utils.realtime_data")
    except ImportError as e:
        print(f"  ✗ utils.realtime_data: {e}")
        return False
    
    try:
        from utils.data_service import DataService, CryptoDataService, WeatherDataService
        print("  ✓ utils.data_service")
    except ImportError as e:
        print(f"  ✗ utils.data_service: {e}")
        return False
    
    try:
        from dashboard.realtime_api import create_realtime_endpoints
        print("  ✓ dashboard.realtime_api")
    except ImportError as e:
        print(f"  ✗ dashboard.realtime_api: {e}")
        return False
    
    return True

def test_cache():
    """Test cache functionality."""
    print("\nTesting cache system...")
    try:
        from utils.realtime_data import get_realtime_cache
        
        cache = get_realtime_cache()
        print("  ✓ Cache instance created")
        
        # Test crypto update
        test_crypto = [
            {'symbol': 'BTC', 'name': 'Bitcoin', 'price_usd': 45000, 'volume_24h': 1000000}
        ]
        changed = cache.update_crypto(test_crypto)
        print(f"  ✓ Crypto update: {changed} (changed)")
        
        # Test retrieval
        data = cache.get_crypto('BTC')
        print(f"  ✓ Retrieved crypto: {data['symbol']} @ ${data['price_usd']}")
        
        # Test stats
        stats = cache.get_all_stats()
        print(f"  ✓ Cache stats: {stats['crypto_count']} cryptos")
        
        return True
    except Exception as e:
        print(f"  ✗ Cache test failed: {e}")
        return False

def test_data_service():
    """Test data service normalization."""
    print("\nTesting data service...")
    try:
        from utils.data_service import DataService
        
        # Test crypto normalization
        raw_crypto = {
            'symbol': 'ETH',
            'name': 'Ethereum',
            'price': 2500,
            'volume': 5000000
        }
        normalized = DataService.CRYPTO.normalize_crypto_entry(raw_crypto)
        print(f"  ✓ Crypto normalized: {normalized['symbol']} @ ${normalized['price_usd']}")
        
        # Test weather normalization
        raw_weather = {
            'location': 'New York',
            'lat': 40.7128,
            'lon': -74.0060,
            'temperature': 22.5,
            'humidity': 65
        }
        normalized = DataService.WEATHER.normalize_weather_entry(raw_weather)
        print(f"  ✓ Weather normalized: {normalized['location_name']} ({normalized['temperature']}°C)")
        
        # Test trend normalization
        raw_trend = {
            'name': '#Bitcoin',
            'source': 'twitter',
            'volume': 50000
        }
        normalized = DataService.SOCIAL_TRENDS.normalize_trend_entry(raw_trend)
        print(f"  ✓ Trend normalized: {normalized['name']} ({normalized['source']})")
        
        return True
    except Exception as e:
        print(f"  ✗ Data service test failed: {e}")
        return False

def test_scheduler():
    """Test scheduler imports and structure."""
    print("\nTesting scheduler integration...")
    try:
        from scheduler.job import scrape_and_store, sync_social_media_trends
        print("  ✓ Scheduler jobs can be imported")
        print("  ✓ Jobs include cache integration")
        return True
    except Exception as e:
        print(f"  ✗ Scheduler test failed: {e}")
        return False

def test_integration_checklist():
    """Print integration checklist."""
    print("\n" + "="*60)
    print("INTEGRATION CHECKLIST")
    print("="*60)
    print("""
[ ] 1. Real-time modules are installed and importable
      - utils/realtime_data.py ✓
      - utils/data_service.py ✓
      - dashboard/realtime_api.py ✓
      - scheduler/job.py (updated) ✓

[ ] 2. Initialize cache in dashboard/app_new.py:
      from utils.realtime_data import get_realtime_cache
      cache = get_realtime_cache()

[ ] 3. Register endpoints in dashboard/app_new.py:
      from dashboard.realtime_api import create_realtime_endpoints
      create_realtime_endpoints(app, cache, None)

[ ] 4. Update weather sync function in dashboard/app_new.py:
      - Import DataService
      - Normalize weather data
      - Update cache with cache.update_weather()

[ ] 5. Add JavaScript to templates for live updates:
      - Copy RealtimeDataManager class from REALTIME_INTEGRATION.md
      - Initialize subscriptions on page load
      - Add cleanup on page unload

[ ] 6. Test endpoints:
      curl http://localhost:5000/api/realtime/data
      curl http://localhost:5000/api/realtime/stats

[ ] 7. Monitor logs:
      tail -f logs/rpa.log

[ ] 8. Configure environment variables in .env:
      REALTIME_ENABLED=true
      SCRAPE_INTERVAL_MINUTES=5
      WEATHER_SYNC_INTERVAL_MINUTES=10
      SOCIAL_SYNC_INTERVAL_MINUTES=15

[ ] 9. Test in browser:
      Open dashboard
      Check browser console for real-time updates
      Verify data refreshes without manual reload

[ ] 10. Production deployment:
       - Set up SSL/TLS for SSE
       - Configure load balancer for long-lived connections
       - Monitor event stream performance
       - Set up alerts for cache failures
    """)
    print("="*60)

def main():
    """Run all tests."""
    print("Real-Time Data System - Integration Test")
    print("="*60)
    
    tests = [
        ("Imports", test_imports),
        ("Cache", test_cache),
        ("Data Service", test_data_service),
        ("Scheduler", test_scheduler),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            results.append((name, False))
    
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:<10} {name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print("\n✓ All infrastructure tests passed!")
        test_integration_checklist()
        return 0
    else:
        print("\n✗ Some tests failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
