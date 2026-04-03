# Configuration settings
DATABASE_HOST = 'localhost'
DATABASE_USER = 'your_username'
DATABASE_PASSWORD = 'your_password'
DATABASE_NAME = 'crypto_data'

# CoinMarketCap API (if using)
CMC_API_KEY = 'your_api_key'

# Scraping settings
# CoinGecko free API rate limit: ~50 req/min, but uses quota system
# Setting to 5 minutes to stay well under limits
SCRAPE_INTERVAL_MINUTES = 1

# Weather sync interval (minutes). Can be overridden with
# environment variable WEATHER_SYNC_INTERVAL_MINUTES
WEATHER_SYNC_INTERVAL_MINUTES = 1

# Social media sync interval (minutes). Can be overridden with
# environment variable SOCIAL_SYNC_INTERVAL_MINUTES
SOCIAL_SYNC_INTERVAL_MINUTES = 1

# Logging
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/rpa.log'