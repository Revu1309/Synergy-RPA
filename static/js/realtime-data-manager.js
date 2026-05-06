/**
 * Real-Time Data Manager - Complete Frontend Integration
 * Copy this code into your base template or main JavaScript file
 */

class RealtimeDataManager {
    /**
     * Manages real-time data connections and updates
     */
    constructor(options = {}) {
        this.baseUrl = options.baseUrl || '/api/realtime';
        this.subscriptions = new Map();
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
        this.reconnectDelay = options.reconnectDelay || 3000;
        this.pollInterval = options.pollInterval || 10000;
        this.enablePolling = options.enablePolling !== false;
        this.debug = options.debug || false;
    }

    log(message, ...args) {
        if (this.debug) {
            console.log(`[RealtimeDataManager] ${message}`, ...args);
        }
    }

    error(message, ...args) {
        console.error(`[RealtimeDataManager] ${message}`, ...args);
    }

    /**
     * Subscribe to real-time events via Server-Sent Events (SSE)
     * @param {string} endpoint - API endpoint path (e.g., 'crypto-stream')
     * @param {Function} callback - Called when new data arrives
     * @param {Function} errorCallback - Called on error
     * @param {boolean} useFallback - Fallback to polling if SSE fails
     */
    subscribe(endpoint, callback, errorCallback = null, useFallback = true) {
        const fullUrl = `${this.baseUrl}/${endpoint}`;
        this.log(`Subscribing to ${fullUrl}`);

        try {
            const eventSource = new EventSource(fullUrl);

            eventSource.addEventListener('connected', () => {
                this.log(`Connected to ${endpoint}`);
                this.connected = true;
                this.reconnectAttempts = 0;
            });

            eventSource.addEventListener('error', () => {
                this.log(`Error on ${endpoint} stream`);
                this.connected = false;
                eventSource.close();

                if (useFallback && this.enablePolling) {
                    this.error(`SSE stream failed for ${endpoint}, falling back to polling`);
                    this.pollEndpoint(endpoint, callback, errorCallback);
                } else if (errorCallback) {
                    errorCallback(new Error('SSE connection failed'));
                }
            });

            eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.log(`Received ${endpoint} update:`, data);
                    callback(data);
                } catch (e) {
                    this.error(`Failed to parse event data from ${endpoint}:`, e);
                    if (errorCallback) errorCallback(e);
                }
            };

            this.subscriptions.set(endpoint, eventSource);
            return eventSource;

        } catch (e) {
            this.error(`Failed to subscribe to ${endpoint}:`, e);
            if (errorCallback) errorCallback(e);
            
            // Fallback to polling
            if (useFallback && this.enablePolling) {
                this.log(`SSE not supported, using polling for ${endpoint}`);
                this.pollEndpoint(endpoint, callback, errorCallback);
            }
        }
    }

    /**
     * Fetch data via polling (fallback for SSE)
     * @private
     */
    async pollEndpoint(endpoint, callback, errorCallback) {
        const endpointName = endpoint.replace('-stream', '');
        const pollUrl = `${this.baseUrl}/${endpointName}`;

        const poll = async () => {
            try {
                const response = await fetch(pollUrl);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                
                const data = await response.json();
                if (data.success) {
                    callback(data.data);
                } else {
                    throw new Error(data.error);
                }
            } catch (e) {
                this.error(`Polling failed for ${endpointName}:`, e);
                if (errorCallback) errorCallback(e);
            }
        };

        // Initial poll
        await poll();

        // Poll periodically
        const pollId = setInterval(poll, this.pollInterval);
        this.subscriptions.set(`${endpoint}-poll`, { close: () => clearInterval(pollId) });
    }

    /**
     * Fetch a single data snapshot (one-time request)
     * @param {string} endpoint - Endpoint name (e.g., 'crypto', 'weather')
     * @param {object} params - Query parameters
     * @returns {Promise<object>} Response data
     */
    async fetchData(endpoint, params = {}) {
        const url = new URL(`${this.baseUrl}/${endpoint}`, window.location.origin);
        Object.entries(params).forEach(([key, value]) => {
            if (value) url.searchParams.append(key, value);
        });

        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (e) {
            this.error(`Failed to fetch ${endpoint}:`, e);
            throw e;
        }
    }

    /**
     * Get current statistics
     * @returns {Promise<object>} Cache stats
     */
    async getStats() {
        return this.fetchData('stats');
    }

    /**
     * Unsubscribe from a specific endpoint
     */
    unsubscribe(endpoint) {
        const subscription = this.subscriptions.get(endpoint);
        if (subscription) {
            subscription.close();
            this.subscriptions.delete(endpoint);
            this.log(`Unsubscribed from ${endpoint}`);
        }
    }

    /**
     * Unsubscribe from all endpoints
     */
    closeAll() {
        for (const [endpoint, subscription] of this.subscriptions) {
            try {
                subscription.close();
            } catch (e) {
                this.error(`Error closing ${endpoint}:`, e);
            }
        }
        this.subscriptions.clear();
        this.connected = false;
        this.log('All subscriptions closed');
    }

    /**
     * Check connection status
     */
    isConnected() {
        return this.connected;
    }

    /**
     * Get connection status details
     */
    async getConnectionStatus() {
        try {
            const stats = await this.getStats();
            return {
                connected: this.connected,
                stats: stats.data,
                timestamp: stats.timestamp
            };
        } catch (e) {
            return {
                connected: false,
                error: e.message,
                timestamp: new Date().toISOString()
            };
        }
    }
}

/**
 * Example Usage
 */

// Initialize the manager
const rtManager = new RealtimeDataManager({
    debug: true,
    enablePolling: true,
    pollInterval: 10000,
    baseUrl: '/api/realtime'
});

/**
 * Example 1: Real-time Crypto Updates
 */
function setupCryptoRealtimeUpdates() {
    rtManager.subscribe(
        'crypto-stream',
        (data) => {
            console.log('Crypto update:', data);
            updateCryptoUI(data);
        },
        (error) => {
            console.error('Crypto stream error:', error);
            // UI update will use polling fallback
        }
    );
}

function updateCryptoUI(data) {
    const container = document.getElementById('crypto-container');
    if (!container) return;

    container.innerHTML = '';
    
    if (data.assets && Array.isArray(data.assets)) {
        data.assets.forEach(asset => {
            const card = document.createElement('div');
            card.className = 'crypto-card';
            card.innerHTML = `
                <div class="crypto-symbol">${asset.symbol}</div>
                <div class="crypto-name">${asset.name}</div>
                <div class="crypto-price">$${asset.price_usd?.toFixed(2) || 'N/A'}</div>
                <div class="crypto-volume">${asset.volume_24h?.toLocaleString() || 'N/A'}</div>
                <div class="crypto-updated">${new Date(asset.timestamp).toLocaleTimeString()}</div>
            `;
            container.appendChild(card);
        });
    }
}

/**
 * Example 2: Real-time Weather Updates
 */
function setupWeatherRealtimeUpdates() {
    rtManager.subscribe(
        'weather-stream',
        (data) => {
            console.log('Weather update:', data);
            updateWeatherUI(data);
        }
    );
}

function updateWeatherUI(data) {
    const container = document.getElementById('weather-container');
    if (!container) return;

    container.innerHTML = '';
    
    if (data.locations && typeof data.locations === 'object') {
        Object.entries(data.locations).forEach(([location, weather]) => {
            const card = document.createElement('div');
            card.className = 'weather-card';
            card.innerHTML = `
                <div class="weather-location">${location}</div>
                <div class="weather-temp">${weather.temperature?.toFixed(1) || 'N/A'}°C</div>
                <div class="weather-condition">${weather.weather_main || 'N/A'}</div>
                <div class="weather-humidity">Humidity: ${weather.humidity || 'N/A'}%</div>
                <div class="weather-wind">Wind: ${weather.wind_speed?.toFixed(1) || 'N/A'} m/s</div>
            `;
            container.appendChild(card);
        });
    }
}

/**
 * Example 3: Real-time Social Trends
 */
function setupSocialTrendsRealtimeUpdates() {
    rtManager.subscribe(
        'social-stream',
        (data) => {
            console.log('Social trends update:', data);
            updateSocialUI(data);
        }
    );
}

function updateSocialUI(data) {
    const container = document.getElementById('social-container');
    if (!container) return;

    container.innerHTML = '';
    
    if (data.trends && Array.isArray(data.trends)) {
        data.trends.slice(0, 10).forEach((trend, index) => {
            const item = document.createElement('div');
            item.className = 'trend-item';
            item.innerHTML = `
                <div class="trend-rank">#${index + 1}</div>
                <div class="trend-name">${trend.name}</div>
                <div class="trend-source">${trend.source}</div>
                <div class="trend-volume">${trend.tweet_volume?.toLocaleString() || 0} mentions</div>
            `;
            container.appendChild(item);
        });
    }
}

/**
 * Example 4: Signal Fusion Index
 */
async function updateSignalFusion() {
    try {
        const response = await rtManager.fetchData('signal-fusion');
        if (response.success && response.data) {
            const fusion = response.data;
            const container = document.getElementById('signal-fusion-container');
            if (container) {
                container.innerHTML = `
                    <div class="fusion-score">${(fusion.fusion_score * 100).toFixed(1)}%</div>
                    <div class="fusion-components">
                        <span>Crypto: ${(fusion.crypto_score * 100).toFixed(0)}%</span>
                        <span>Social: ${(fusion.social_score * 100).toFixed(0)}%</span>
                        <span>Weather: ${(fusion.weather_score * 100).toFixed(0)}%</span>
                    </div>
                    <div class="fusion-confidence">Confidence: ${fusion.confidence_level}</div>
                `;
            }
        }
    } catch (e) {
        console.error('Failed to fetch signal fusion:', e);
    }
}

/**
 * Example 5: Monitor System Health
 */
async function monitorSystemHealth() {
    setInterval(async () => {
        const status = await rtManager.getConnectionStatus();
        console.log('System status:', status);
        
        // Update UI with connection indicator
        const indicator = document.getElementById('connection-indicator');
        if (indicator) {
            indicator.className = status.connected ? 'connected' : 'disconnected';
            indicator.title = `${status.connected ? 'Connected' : 'Disconnected'} - ${new Date().toLocaleTimeString()}`;
        }
    }, 30000); // Check every 30 seconds
}

/**
 * Setup on DOM Ready
 */
document.addEventListener('DOMContentLoaded', () => {
    // Initialize all real-time updates
    setupCryptoRealtimeUpdates();
    setupWeatherRealtimeUpdates();
    setupSocialTrendsRealtimeUpdates();
    updateSignalFusion();
    monitorSystemHealth();
});

/**
 * Cleanup on page unload
 */
window.addEventListener('beforeunload', () => {
    rtManager.closeAll();
});

/**
 * CSS Styling Suggestions
 */
const styles = `
<style>
.crypto-card, .weather-card, .trend-item {
    padding: 1rem;
    margin: 0.5rem;
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.3s ease;
}

.crypto-card:hover, .weather-card:hover, .trend-item:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(91, 91, 255, 0.4);
}

.connection-indicator {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 8px;
}

.connection-indicator.connected {
    background: #4ade80;
    box-shadow: 0 0 10px rgba(74, 222, 128, 0.5);
}

.connection-indicator.disconnected {
    background: #ef4444;
    box-shadow: 0 0 10px rgba(239, 68, 68, 0.5);
}

.realtime-updated {
    animation: pulse 0.5s ease-in-out;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.7; }
    100% { opacity: 1; }
}
</style>
`;

/**
 * Export for use in modules
 */
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RealtimeDataManager;
}
