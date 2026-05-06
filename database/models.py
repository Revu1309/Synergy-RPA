from .connection import create_connection, get_cursor, is_postgres

def insert_crypto_data(symbol, name, price_usd, market_cap, volume_24h):
    """Insert crypto data into the database."""
    connection = create_connection()
    if connection:
        cursor = get_cursor(connection)
        try:
            query = """
                INSERT INTO crypto_assets (symbol, name, price_usd, market_cap, volume_24h)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (symbol, name, price_usd, market_cap, volume_24h))
            connection.commit()
        finally:
            cursor.close()
            connection.close()

def upsert_crypto_latest(symbol, name, price_usd, market_cap, volume_24h):
    """Atomically upsert latest crypto snapshot into `crypto_latest`."""
    connection = create_connection()
    if connection:
        cursor = get_cursor(connection)
        try:
            if is_postgres(connection):
                query = """
                INSERT INTO crypto_latest (symbol, name, price_usd, market_cap, volume_24h, last_updated)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (symbol) DO UPDATE SET
                    name = EXCLUDED.name,
                    price_usd = EXCLUDED.price_usd,
                    market_cap = EXCLUDED.market_cap,
                    volume_24h = EXCLUDED.volume_24h,
                    last_updated = CURRENT_TIMESTAMP
                """
            else:
                query = """
                INSERT INTO crypto_latest (symbol, name, price_usd, market_cap, volume_24h, last_updated)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                    name = VALUES(name),
                    price_usd = VALUES(price_usd),
                    market_cap = VALUES(market_cap),
                    volume_24h = VALUES(volume_24h),
                    last_updated = NOW()
                """
            cursor.execute(query, (symbol, name, price_usd, market_cap, volume_24h))
            connection.commit()
        finally:
            cursor.close()
            connection.close()

def clear_crypto_data():
    """Clear all cryptocurrency data from the crypto_assets table."""
    connection = create_connection()
    if connection:
        cursor = get_cursor(connection)
        try:
            cursor.execute("DELETE FROM crypto_assets")
            connection.commit()
            print("✓ Cleared all cryptocurrency data")
        except Exception as e:
            print(f"Error clearing crypto data: {e}")
        finally:
            cursor.close()
            connection.close()

# ==================== WEATHER DATA MODELS ====================

def insert_weather_data(location_name, country, latitude, longitude, temperature, 
                       feels_like, humidity, pressure, wind_speed, wind_direction,
                       cloudiness, weather_main, weather_description, visibility, 
                       rainfall, snow):
    """Insert weather data into the database."""
    connection = create_connection()
    if connection:
        cursor = get_cursor(connection)
        try:
            query = """
                INSERT INTO weather_data 
                (location_name, country, latitude, longitude, temperature, feels_like, 
                 humidity, pressure, wind_speed, wind_direction, cloudiness, 
                 weather_main, weather_description, visibility, rainfall, snow)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (location_name, country, latitude, longitude, temperature,
                                  feels_like, humidity, pressure, wind_speed, wind_direction,
                                  cloudiness, weather_main, weather_description, visibility,
                                  rainfall, snow))
            connection.commit()
        finally:
            cursor.close()
            connection.close()

def upsert_weather_latest(location_name, country, latitude, longitude, temperature,
                          feels_like, humidity, pressure, wind_speed, wind_direction,
                          cloudiness, weather_main, weather_description, visibility,
                          rainfall, snow):
    """Atomically upsert latest weather snapshot into `weather_latest`."""
    connection = create_connection()
    if connection:
        cursor = get_cursor(connection)
        try:
            if is_postgres(connection):
                query = """
                INSERT INTO weather_latest
                (location_name, country, latitude, longitude, temperature, feels_like, humidity,
                 pressure, wind_speed, wind_direction, cloudiness, weather_main, weather_description,
                 visibility, rainfall, snow, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (location_name) DO UPDATE SET
                    country = EXCLUDED.country,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    temperature = EXCLUDED.temperature,
                    feels_like = EXCLUDED.feels_like,
                    humidity = EXCLUDED.humidity,
                    pressure = EXCLUDED.pressure,
                    wind_speed = EXCLUDED.wind_speed,
                    wind_direction = EXCLUDED.wind_direction,
                    cloudiness = EXCLUDED.cloudiness,
                    weather_main = EXCLUDED.weather_main,
                    weather_description = EXCLUDED.weather_description,
                    visibility = EXCLUDED.visibility,
                    rainfall = EXCLUDED.rainfall,
                    snow = EXCLUDED.snow,
                    last_updated = CURRENT_TIMESTAMP
                """
            else:
                query = """
                INSERT INTO weather_latest
                (location_name, country, latitude, longitude, temperature, feels_like, humidity,
                 pressure, wind_speed, wind_direction, cloudiness, weather_main, weather_description,
                 visibility, rainfall, snow, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                    country = VALUES(country),
                    latitude = VALUES(latitude),
                    longitude = VALUES(longitude),
                    temperature = VALUES(temperature),
                    feels_like = VALUES(feels_like),
                    humidity = VALUES(humidity),
                    pressure = VALUES(pressure),
                    wind_speed = VALUES(wind_speed),
                    wind_direction = VALUES(wind_direction),
                    cloudiness = VALUES(cloudiness),
                    weather_main = VALUES(weather_main),
                    weather_description = VALUES(weather_description),
                    visibility = VALUES(visibility),
                    rainfall = VALUES(rainfall),
                    snow = VALUES(snow),
                    last_updated = NOW()
                """
            cursor.execute(query, (location_name, country, latitude, longitude, temperature,
                                   feels_like, humidity, pressure, wind_speed, wind_direction,
                                   cloudiness, weather_main, weather_description, visibility,
                                   rainfall, snow))
            connection.commit()
        finally:
            cursor.close()
            connection.close()

def get_latest_weather_data(location_name=None):
    """Get latest weather data for location(s)."""
    connection = create_connection()
    if connection:
        cursor = get_cursor(connection)
        if location_name:
            query = """
                SELECT * FROM weather_data 
                WHERE location_name = %s 
                ORDER BY timestamp DESC LIMIT 1
            """
            cursor.execute(query, (location_name,))
        else:
            if is_postgres(connection):
                query = """
                    SELECT DISTINCT ON (location_name) * FROM weather_data 
                    ORDER BY location_name, timestamp DESC
                """
            else:
                query = """
                    SELECT * FROM weather_data 
                    WHERE (location_name, timestamp) IN (
                        SELECT location_name, MAX(timestamp) 
                        FROM weather_data GROUP BY location_name
                    )
                """
            cursor.execute(query)
        
        result = cursor.fetchall()
        cursor.close()
        connection.close()
        return result
    return None

def get_latest_crypto():
    """Return all records from `crypto_latest` as a list of dicts."""
    connection = create_connection()
    if connection:
        cursor = get_cursor(connection, dictionary=True)
        cursor.execute("SELECT symbol, name, price_usd, market_cap, volume_24h, last_updated FROM crypto_latest")
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        return rows
    return []

def get_latest_weather():
    """Return all records from `weather_latest` as a list of dicts."""
    connection = create_connection()
    if connection:
        cursor = get_cursor(connection, dictionary=True)
        cursor.execute("SELECT * FROM weather_latest")
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        return rows
    return []

def upsert_social_latest(trend_name, source_platform, rank_position, volume, engagement_count, sentiment, trend_url=None):
    """Upsert social trend snapshot into `social_latest`."""
    key = f"{source_platform}::{trend_name}"
    connection = create_connection()
    if connection:
        cursor = get_cursor(connection)
        try:
            if is_postgres(connection):
                query = """
                INSERT INTO social_latest (trend_key, trend_name, source_platform, rank_position, volume, engagement_count, sentiment, trend_url, data_collected_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (trend_key) DO UPDATE SET
                    rank_position = EXCLUDED.rank_position,
                    volume = EXCLUDED.volume,
                    engagement_count = EXCLUDED.engagement_count,
                    sentiment = EXCLUDED.sentiment,
                    trend_url = EXCLUDED.trend_url,
                    data_collected_at = CURRENT_TIMESTAMP
                """
            else:
                query = """
                INSERT INTO social_latest (trend_key, trend_name, source_platform, rank_position, volume, engagement_count, sentiment, trend_url, data_collected_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                    rank_position = VALUES(rank_position),
                    volume = VALUES(volume),
                    engagement_count = VALUES(engagement_count),
                    sentiment = VALUES(sentiment),
                    trend_url = VALUES(trend_url),
                    data_collected_at = NOW()
                """
            cursor.execute(query, (key, trend_name, source_platform, rank_position, volume, engagement_count, sentiment, trend_url))
            connection.commit()
        finally:
            cursor.close()
            connection.close()

def get_latest_social():
    connection = create_connection()
    if connection:
        cursor = get_cursor(connection, dictionary=True)
        cursor.execute("SELECT * FROM social_latest")
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        return rows
    return []

def get_weather_history(location_name, days=7):
    """Get weather history for a location."""
    connection = create_connection()
    if connection:
        cursor = get_cursor(connection)
        if is_postgres(connection):
            query = """
                SELECT * FROM weather_data 
                WHERE location_name = %s 
                AND timestamp >= CURRENT_TIMESTAMP - (INTERVAL '1 day' * %s)
                ORDER BY timestamp DESC
            """
        else:
            query = """
                SELECT * FROM weather_data 
                WHERE location_name = %s 
                AND timestamp >= NOW() - INTERVAL '1 DAY' * %s
                ORDER BY timestamp DESC
            """
        cursor.execute(query, (location_name, days))
        result = cursor.fetchall()
        cursor.close()
        connection.close()
        return result
    return None

def insert_signal_fusion_index(crypto_score, social_score, weather_score, fusion_score, confidence_level):
    """Insert one Signal Fusion Index snapshot row."""
    connection = create_connection()
    if connection:
        cursor = get_cursor(connection)
        try:
            if is_postgres(connection):
                query = """
                INSERT INTO signal_fusion_index
                (crypto_score, social_score, weather_score, fusion_score, confidence_level, timestamp)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                """
            else:
                query = """
                INSERT INTO signal_fusion_index
                (crypto_score, social_score, weather_score, fusion_score, confidence_level, timestamp)
                VALUES (%s, %s, %s, %s, %s, NOW())
                """
            cursor.execute(query, (crypto_score, social_score, weather_score, fusion_score, confidence_level))
            connection.commit()
        finally:
            cursor.close()
            connection.close()

def get_signal_fusion_index(hours=24):
    """Read historical Signal Fusion Index snapshots."""
    connection = create_connection()
    if connection:
        cursor = get_cursor(connection, dictionary=True)
        try:
            if is_postgres(connection):
                query = """
                SELECT timestamp, crypto_score, social_score, weather_score, fusion_score, confidence_level
                FROM signal_fusion_index
                WHERE timestamp >= CURRENT_TIMESTAMP - (INTERVAL '1 hour' * %s)
                ORDER BY timestamp ASC
                """
            else:
                query = """
                SELECT timestamp, crypto_score, social_score, weather_score, fusion_score, confidence_level
                FROM signal_fusion_index
                WHERE timestamp >= NOW() - (INTERVAL '1 hour' * %s)
                ORDER BY timestamp ASC
                """
            cursor.execute(query, (hours,))
            return cursor.fetchall()
        finally:
            cursor.close()
            connection.close()
    return []
