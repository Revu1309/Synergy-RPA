import os
import mysql.connector
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None

from dotenv import load_dotenv

load_dotenv()

def create_connection():
    """Create a database connection (supports both MySQL and Vercel Postgres)."""
    # 1. Try Vercel Postgres first (standard environment variable)
    postgres_url = os.getenv('POSTGRES_URL') or os.getenv('DATABASE_URL')
    
    if postgres_url and postgres_url.startswith('postgres'):
        if psycopg2 is None:
            print("Error: psycopg2-binary not installed for Postgres support.")
            return None
        try:
            # Vercel Postgres often needs SSL
            connection = psycopg2.connect(postgres_url, sslmode='require')
            connection.autocommit = True
            return connection
        except Exception as e:
            print(f"Postgres Connection Error: {e}")
            # Fall back to MySQL if Postgres fails
    
    # 2. Fall back to MySQL
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DATABASE_HOST', 'localhost'),
            user=os.getenv('DATABASE_USER', 'rpauser'),
            password=os.getenv('DATABASE_PASSWORD', 'rpauser'),
            database=os.getenv('DATABASE_NAME', 'crypto_data'),
            autocommit=True
        )
        return connection
    except Exception as e:
        print(f"MySQL Connection Error: {e}")
        return None

def is_postgres(connection):
    """Check if the connection is a Postgres connection."""
    if psycopg2 and isinstance(connection, psycopg2.extensions.connection):
        return True
    return False

def get_cursor(connection, dictionary=False):
    """Get a cursor that behaves similarly across MySQL and Postgres."""
    if is_postgres(connection):
        if dictionary:
            return connection.cursor(cursor_factory=RealDictCursor)
        return connection.cursor()
    else:
        if dictionary:
            return connection.cursor(dictionary=True)
        return connection.cursor()

def create_table():
    """Create the crypto_assets table."""
    conn = create_connection()
    if not conn: return
    cursor = get_cursor(conn)
    
    if is_postgres(conn):
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crypto_assets (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                name VARCHAR(100) NOT NULL,
                price_usd DECIMAL(20, 8),
                market_cap BIGINT,
                volume_24h BIGINT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_crypto_ts ON crypto_assets(timestamp)")
    else:
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
    conn.commit()
    cursor.close()
    conn.close()

def create_crypto_latest_table():
    conn = create_connection()
    if not conn: return
    cursor = get_cursor(conn)
    
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
    conn.commit()
    cursor.close()
    conn.close()

def create_weather_table():
    conn = create_connection()
    if not conn: return
    cursor = get_cursor(conn)
    
    if is_postgres(conn):
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather_data (
                id SERIAL PRIMARY KEY,
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
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_weather_loc ON weather_data(location_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_weather_ts ON weather_data(timestamp)")
    else:
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
    conn.commit()
    cursor.close()
    conn.close()

def create_weather_latest_table():
    conn = create_connection()
    if not conn: return
    cursor = get_cursor(conn)
    
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
    conn.commit()
    cursor.close()
    conn.close()

def create_social_latest_table():
    conn = create_connection()
    if not conn: return
    cursor = get_cursor(conn)
    
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
    conn.commit()
    cursor.close()
    conn.close()

def create_weather_locations_table():
    conn = create_connection()
    if not conn: return
    cursor = get_cursor(conn)
    
    if is_postgres(conn):
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather_locations (
                id SERIAL PRIMARY KEY,
                location_name VARCHAR(100) NOT NULL UNIQUE,
                country VARCHAR(100),
                latitude DECIMAL(10, 6) NOT NULL,
                longitude DECIMAL(10, 6) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wloc_active ON weather_locations(is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wloc_name ON weather_locations(location_name)")
    else:
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
    conn.commit()
    cursor.close()
    conn.close()

def create_signal_fusion_index_table():
    conn = create_connection()
    if not conn: return
    cursor = get_cursor(conn)
    
    if is_postgres(conn):
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signal_fusion_index (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                crypto_score DECIMAL(6,2) NOT NULL,
                social_score DECIMAL(6,2) NOT NULL,
                weather_score DECIMAL(6,2) NOT NULL,
                fusion_score DECIMAL(6,2) NOT NULL,
                confidence_level VARCHAR(20) NOT NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fusion_ts ON signal_fusion_index(timestamp)")
    else:
        cursor.execute("""
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
        """)
    conn.commit()
    cursor.close()
    conn.close()
