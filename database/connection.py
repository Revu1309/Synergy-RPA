import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

def create_connection():
    """Create a database connection."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DATABASE_HOST'),
            user=os.getenv('DATABASE_USER'),
            password=os.getenv('DATABASE_PASSWORD'),
            database=os.getenv('DATABASE_NAME'),
            autocommit=True
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error: {e}")
        return None

def create_table():
    """Create the crypto_assets table if it doesn't exist."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crypto_assets (
                id INT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                name VARCHAR(100) NOT NULL,
                price_usd DECIMAL(20, 8),
                market_cap BIGINT,
                volume_24h BIGINT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.commit()
        cursor.close()
        connection.close()

def create_crypto_latest_table():
    """Create a table holding the latest snapshot per symbol for fast reads."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crypto_latest (
                symbol VARCHAR(10) PRIMARY KEY,
                name VARCHAR(100),
                price_usd DECIMAL(20,8),
                market_cap BIGINT,
                volume_24h BIGINT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.commit()
        cursor.close()
        connection.close()

def create_weather_table():
    """Create the weather_data table if it doesn't exist."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                location_name VARCHAR(100) NOT NULL,
                country VARCHAR(100),
                latitude DECIMAL(10, 6),
                longitude DECIMAL(10, 6),
                temperature DECIMAL(5, 2),
                feels_like DECIMAL(5, 2),
                humidity INT,
                pressure INT,
                wind_speed DECIMAL(6, 2),
                wind_direction INT,
                cloudiness INT,
                weather_main VARCHAR(50),
                weather_description VARCHAR(200),
                visibility INT,
                rainfall DECIMAL(6, 2),
                snow DECIMAL(6, 2),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_location (location_name),
                INDEX idx_timestamp (timestamp)
            )
        """)
        connection.commit()
        cursor.close()
        connection.close()

def create_weather_latest_table():
    """Create a table holding the latest weather snapshot per location."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather_latest (
                location_name VARCHAR(100) PRIMARY KEY,
                country VARCHAR(100),
                latitude DECIMAL(10,6),
                longitude DECIMAL(10,6),
                temperature DECIMAL(5,2),
                feels_like DECIMAL(5,2),
                humidity INT,
                pressure INT,
                wind_speed DECIMAL(6,2),
                wind_direction INT,
                cloudiness INT,
                weather_main VARCHAR(50),
                weather_description VARCHAR(200),
                visibility INT,
                rainfall DECIMAL(6,2),
                snow DECIMAL(6,2),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.commit()
        cursor.close()
        connection.close()

def create_social_latest_table():
    """Create a table holding the latest social trend snapshot per trend+platform."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS social_latest (
                    trend_key VARCHAR(300) PRIMARY KEY,
                    trend_name VARCHAR(255),
                    source_platform VARCHAR(50),
                    rank_position INT,
                    volume INT,
                    engagement_count BIGINT,
                    sentiment VARCHAR(20),
                    trend_url VARCHAR(1000),
                    data_collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Safe migration for existing deployments.
            try:
                cursor.execute("ALTER TABLE social_latest ADD COLUMN trend_url VARCHAR(1000) NULL")
            except Exception:
                pass
            connection.commit()
        finally:
            cursor.close()
            connection.close()

def create_weather_locations_table():
    """Create the weather_locations table if it doesn't exist."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather_locations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                location_name VARCHAR(100) NOT NULL UNIQUE,
                country VARCHAR(100),
                latitude DECIMAL(10, 6) NOT NULL,
                longitude DECIMAL(10, 6) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                notes TEXT,
                INDEX idx_active (is_active),
                INDEX idx_location_name (location_name)
            )
        """)
        connection.commit()
        cursor.close()
        connection.close()


def create_signal_fusion_index_table():
    """Create table storing historical Signal Fusion Index snapshots."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS signal_fusion_index (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                crypto_score DECIMAL(6,2) NOT NULL,
                social_score DECIMAL(6,2) NOT NULL,
                weather_score DECIMAL(6,2) NOT NULL,
                fusion_score DECIMAL(6,2) NOT NULL,
                confidence_level VARCHAR(20) NOT NULL,
                INDEX idx_timestamp (timestamp)
            )
            """
        )
        connection.commit()
        cursor.close()
        connection.close()
