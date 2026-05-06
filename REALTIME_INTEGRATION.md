# Real-Time Data Integration & Project Consistency Report

## Overview
This document outlines all the changes made to bring real-time data to your Synergy RPA project and make it consistent across all data sources (crypto, weather, social trends).

## Changes Implemented

### 1. **Real-Time Data Cache System** (`utils/realtime_data.py`) ✅
- **Thread-safe data caching** with `RealtimeDataCache` class
- **Change detection** using MD5 hashing to only notify subscribers when data actually changes
- **Subscriber pattern** for efficient event-driven updates
- **Categories supported:**
  - Crypto assets
  - Weather data
  - Social trends
  - Signal fusion index
  - Job status

**Key Features:**
- Prevents redundant notifications
- Thread-safe locks for concurrent access
- Memory-efficient with change tracking
- Centralized cache instance

### 2. **Unified Data Service** (`utils/data_service.py`) ✅
- **Standardized data normalization** across all sources
- **Flexible field mapping** to handle different API naming conventions
- **Data validation** with helpful error messages
- **Four main service modules:**

#### CryptoDataService
- Normalizes: symbol, name, price_usd, market_cap, volume_24h
- Handles flexible naming (price vs price_usd)
- Validates prices are non-negative
- Automatic timestamp generation

#### WeatherDataService
- Normalizes: location, latitude, longitude, temperature, humidity, pressure, wind, etc.
- Handles flexible location naming (city, location, location_name)
- Supports both metric and imperial conversions
- Validates location coordinates

#### SocialTrendDataService
- Normalizes: name, rank, source, volume, sentiment
- Clamps sentiment to [-1, 1]
- Validates source and trend name
- Timestamps all entries

#### JobStatusService
- Normalizes: job_id, job_name, state, progress
- Validates job state (running, completed, failed, pending)
- Clamps progress to [0, 100]

### 3. **Real-Time API Endpoints** (`dashboard/realtime_api.py`) ✅
- **Server-Sent Events (SSE) streams** for live updates
- **JSON snapshots** for on-demand data fetching
- **Endpoints created:**
  - `GET /api/realtime/crypto-stream` - SSE stream for crypto
  - `GET /api/realtime/weather-stream` - SSE stream for weather
  - `GET /api/realtime/social-stream` - SSE stream for trends
  - `GET /api/realtime/data` - All real-time data
  - `GET /api/realtime/crypto` - Crypto JSON snapshot
  - `GET /api/realtime/weather` - Weather JSON snapshot
  - `GET /api/realtime/social` - Social trends JSON snapshot
  - `GET /api/realtime/signal-fusion` - Signal fusion JSON
  - `GET /api/realtime/job-status` - Job status JSON
  - `GET /api/realtime/stats` - Cache statistics

### 4. **Enhanced Scheduler** (`scheduler/job.py`) ✅
- **Data normalization** on every job run
- **Real-time cache integration** updates cache after each sync
- **Better error handling** with granular logging
- **Graceful degradation** if normalization fails
- **Improved logging** with start/end timestamps and operation counts

#### Crypto Sync Job Improvements:
- Validates and normalizes data before insertion
- Updates real-time cache on successful sync
- Logs cache update status
- Individual error handling per record

#### Social Media Sync Job Improvements:
- Normalizes trend data on retrieval
- Updates cache with validated data
- Better error reporting
- Handles partial failures gracefully

---

## Integration Guide

### Step 1: Enable Real-Time Endpoints in `dashboard/app_new.py`

Add these lines near the app initialization (around line 170):

```python
from utils.realtime_data import get_realtime_cache
from dashboard.realtime_api import create_realtime_endpoints

# Initialize real-time cache
cache = get_realtime_cache()

# Register real-time endpoints
create_realtime_endpoints(app, cache, None)
```

### Step 2: Update Weather Sync Job

In `dashboard/app_new.py`, update the `sync_weather_job()` function to normalize data:

```python
def sync_weather_job():
    """Background job to sync weather data with proper timestamps."""
    from utils.data_service import DataService
    from utils.realtime_data import get_realtime_cache
    
    start_ts = datetime.utcnow()
    logging.info(f"[WEATHER] Job start: {start_ts.isoformat()}Z")
    cache = get_realtime_cache()
    
    try:
        locations = WeatherLocationsManager.get_all_locations(active_only=True)
        if not locations:
            locations = []
        
        weather_data = get_weather_data(locations)
        
        # Normalize data
        try:
            normalized_weather = DataService.WEATHER.normalize_weather_list(weather_data)
        except Exception as normalize_err:
            logging.warning(f"[WEATHER] Data normalization warning: {normalize_err}")
            normalized_weather = weather_data
        
        for entry in normalized_weather:
            try:
                insert_weather_data(
                    entry['location_name'], entry['country'],
                    entry['latitude'], entry['longitude'],
                    entry['temperature'], entry['feels_like'],
                    entry['humidity'], entry['pressure'],
                    entry['wind_speed'], entry['wind_direction'],
                    entry['cloudiness'], entry['weather_main'],
                    entry['weather_description'], entry['visibility'],
                    entry['rainfall'], 0  # snow
                )
                upsert_weather_latest(
                    entry['location_name'], entry['country'],
                    entry['latitude'], entry['longitude'],
                    entry['temperature'], entry['feels_like'],
                    entry['humidity'], entry['pressure'],
                    entry['wind_speed'], entry['wind_direction'],
                    entry['cloudiness'], entry['weather_main'],
                    entry['weather_description'], entry['visibility'],
                    entry['rainfall'], 0
                )
            except Exception as item_err:
                logging.warning(f"[WEATHER] Failed to insert {entry.get('location_name')}: {item_err}")
        
        # Update cache
        try:
            weather_dict = {w['location_name']: w for w in normalized_weather}
            cache.update_weather(weather_dict)
            logging.info(f"[WEATHER] Cache updated with {len(normalized_weather)} locations")
        except Exception as cache_err:
            logging.warning(f"[WEATHER] Failed to update cache: {cache_err}")
            
    except Exception as e:
        logging.error(f"[WEATHER] Error syncing weather: {e}")
    finally:
        end_ts = datetime.utcnow()
        logging.info(f"[WEATHER] Job end: {end_ts.isoformat()}Z")
```

### Step 3: Update Frontend JavaScript

Add to your base template or dashboard template:

```html
<script>
// Real-time data connection manager
class RealtimeDataManager {
    constructor() {
        this.subscriptions = new Map();
        this.connected = false;
    }
    
    // Subscribe to server-sent events
    subscribe(endpoint, callback, errorCallback = null) {
        try {
            const eventSource = new EventSource(endpoint);
            
            eventSource.onopen = () => {
                console.log(`Connected to ${endpoint}`);
                this.connected = true;
            };
            
            eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    callback(data);
                } catch (e) {
                    console.error('Failed to parse event data:', e);
                }
            };
            
            eventSource.onerror = (error) => {
                console.error(`Error on ${endpoint}:`, error);
                this.connected = false;
                if (errorCallback) errorCallback(error);
                eventSource.close();
            };
            
            this.subscriptions.set(endpoint, eventSource);
            return eventSource;
        } catch (e) {
            console.error('Failed to subscribe:', e);
            if (errorCallback) errorCallback(e);
        }
    }
    
    // Fetch JSON snapshot
    async fetchData(endpoint) {
        try {
            const response = await fetch(endpoint);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (e) {
            console.error(`Failed to fetch ${endpoint}:`, e);
            return null;
        }
    }
    
    // Unsubscribe from events
    unsubscribe(endpoint) {
        const eventSource = this.subscriptions.get(endpoint);
        if (eventSource) {
            eventSource.close();
            this.subscriptions.delete(endpoint);
        }
    }
    
    // Close all subscriptions
    closeAll() {
        for (const [endpoint, eventSource] of this.subscriptions) {
            eventSource.close();
        }
        this.subscriptions.clear();
        this.connected = false;
    }
}

// Global instance
const rtManager = new RealtimeDataManager();

// Example: Subscribe to crypto updates
function initCryptoRealtimeUpdates() {
    rtManager.subscribe(
        '/api/realtime/crypto-stream',
        (data) => {
            console.log('Crypto update:', data);
            // Update your UI with data.assets
            updateCryptoUI(data.assets);
        },
        (error) => {
            console.error('Crypto stream error:', error);
            // Fall back to polling if SSE fails
            pollCryptoData();
        }
    );
}

// Polling fallback
async function pollCryptoData() {
    const data = await rtManager.fetchData('/api/realtime/crypto');
    if (data && data.success) {
        updateCryptoUI(data.data);
    }
    // Re-poll every 10 seconds
    setTimeout(pollCryptoData, 10000);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initCryptoRealtimeUpdates();
    
    // Optional: Also subscribe to weather and social
    rtManager.subscribe('/api/realtime/weather-stream',
        (data) => updateWeatherUI(data.locations)
    );
    rtManager.subscribe('/api/realtime/social-stream',
        (data) => updateSocialUI(data.trends)
    );
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    rtManager.closeAll();
});
</script>
```

---

## Benefits

### ✅ **Real-Time Updates**
- Data flows from scrapers → database → cache → frontend
- Changes propagate instantly via SSE or polling fallback
- No more manual refresh needed

### ✅ **Consistency**
- All data normalized to standard format
- Flexible field mapping handles API variations
- Validates data before storage

### ✅ **Performance**
- Change detection prevents redundant updates
- Thread-safe caching reduces database queries
- SSE more efficient than polling

### ✅ **Reliability**
- Graceful error handling in scheduler
- Partial sync success (one failure doesn't block all)
- Comprehensive logging for debugging

### ✅ **Scalability**
- Plug-and-play data service modules
- Easy to add new data types
- Clean separation of concerns

---

## Configuration

### Environment Variables to Add (`.env`)

```env
# Real-time Settings
REALTIME_ENABLED=true
CACHE_UPDATE_INTERVAL=30  # seconds between cache refreshes
SSE_KEEPALIVE=30000  # milliseconds between SSE keepalive pings
POLL_INTERVAL=10000  # milliseconds, fallback polling interval

# Sync Intervals (minutes)
SCRAPE_INTERVAL_MINUTES=5
WEATHER_SYNC_INTERVAL_MINUTES=10
SOCIAL_SYNC_INTERVAL_MINUTES=15
```

### Configuration in `config/config.py`

```python
# Real-time settings
REALTIME_ENABLED = os.getenv('REALTIME_ENABLED', 'true').lower() == 'true'
CACHE_UPDATE_INTERVAL = int(os.getenv('CACHE_UPDATE_INTERVAL', 30))
SSE_KEEPALIVE = int(os.getenv('SSE_KEEPALIVE', 30000))
POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', 10000))
```

---

## Testing the Integration

### 1. Check Cache Status
```bash
curl http://localhost:5000/api/realtime/stats
```

### 2. Fetch Current Data
```bash
curl http://localhost:5000/api/realtime/data
curl http://localhost:5000/api/realtime/crypto
curl http://localhost:5000/api/realtime/weather
```

### 3. Monitor Logs
```bash
tail -f logs/rpa.log | grep -E "\[CRYPTO\]|\[WEATHER\]|\[SOCIAL\]"
```

### 4. Test SSE in Browser Console
```javascript
// In browser DevTools console
const es = new EventSource('/api/realtime/crypto-stream');
es.onmessage = (e) => console.log(JSON.parse(e.data));
```

---

## Troubleshooting

### "undefined" in Dashboard
**Cause:** Data not synced yet or cache empty
**Fix:** 
1. Check `/api/realtime/stats` to see cache status
2. Verify scheduler is running in logs
3. Check database has data: `SELECT COUNT(*) FROM crypto_assets;`

### SSE Not Connecting
**Cause:** Firewall, proxy, or browser doesn't support SSE
**Fix:**
1. Check browser console for errors
2. Ensure `/api/realtime/crypto-stream` returns `text/event-stream`
3. Client automatically falls back to polling

### High Database Load
**Cause:** Too frequent syncs or missing indexes
**Fix:**
1. Increase sync intervals in config
2. Add indexes: `ALTER TABLE crypto_assets ADD INDEX idx_timestamp (timestamp);`
3. Monitor cache hit rate in stats endpoint

---

## Next Steps

1. **Integrate real-time endpoints** into `dashboard/app_new.py`
2. **Update weather sync** with cache updates
3. **Add frontend JavaScript** to dashboards
4. **Test each data stream** individually
5. **Monitor logs** for any data inconsistencies
6. **Adjust sync intervals** based on your needs

---

## Files Modified/Created

### New Files:
- ✅ `utils/realtime_data.py` - Cache system
- ✅ `utils/data_service.py` - Unified data service
- ✅ `dashboard/realtime_api.py` - API endpoints

### Modified Files:
- ✅ `scheduler/job.py` - Enhanced with cache integration and data normalization

### Files to Modify:
- 📝 `dashboard/app_new.py` - Add real-time endpoints and weather sync integration
- 📝 `dashboard/templates/*.html` - Add real-time JavaScript updates

---

## Support & Debugging

For debugging, enable verbose logging in `utils/logger.py`:

```python
# Set log level to DEBUG
logger.setLevel(logging.DEBUG)
```

Monitor these log patterns:
- `[CRYPTO]` - Crypto scraping and sync
- `[WEATHER]` - Weather data sync
- `[SOCIAL]` - Social trends sync
- `[FUSION]` - Signal fusion index
- `[ALERTS]` - Alert system
- `[CACHE]` - Cache operations

---

**Project Status:** ✅ Real-time data infrastructure complete and ready for integration!
