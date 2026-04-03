"""Predefined Cities Manager - manages the list of cities to monitor."""

from database.connection import create_connection


class PredefinedCitiesManager:
    """Manage predefined cities for weather monitoring."""

    @staticmethod
    def create_table():
        """Create predefined_cities table if it doesn't exist."""
        connection = create_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predefined_cities (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    city_name VARCHAR(100) NOT NULL UNIQUE,
                    country VARCHAR(100) NOT NULL,
                    latitude DECIMAL(10, 6) NOT NULL,
                    longitude DECIMAL(10, 6) NOT NULL,
                    region VARCHAR(100),
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_active (is_active),
                    INDEX idx_country (country)
                )
            """)
            connection.commit()
            cursor.close()
            connection.close()

    @staticmethod
    def get_all_cities(active_only=True):
        """Get all predefined cities."""
        connection = create_connection()
        if connection:
            cursor = connection.cursor()
            if active_only:
                query = "SELECT id, city_name, country, latitude, longitude, region, description FROM predefined_cities WHERE is_active = TRUE ORDER BY country, city_name"
            else:
                query = "SELECT id, city_name, country, latitude, longitude, region, description FROM predefined_cities ORDER BY country, city_name"
            
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            connection.close()
            
            cities = []
            if results:
                for row in results:
                    cities.append({
                        'id': row[0],
                        'city_name': row[1],
                        'country': row[2],
                        'latitude': float(row[3]),
                        'longitude': float(row[4]),
                        'region': row[5],
                        'description': row[6]
                    })
            return cities
        return []

    @staticmethod
    def add_city(city_name, country, latitude, longitude, region=None, description=None):
        """Add a new predefined city."""
        connection = create_connection()
        if connection:
            cursor = connection.cursor()
            try:
                query = """
                    INSERT INTO predefined_cities 
                    (city_name, country, latitude, longitude, region, description)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (city_name, country, latitude, longitude, region, description))
                connection.commit()
                result = True
            except Exception as e:
                print(f"Error adding city: {e}")
                result = False
            finally:
                cursor.close()
                connection.close()
            return result
        return False

    @staticmethod
    def initialize_default_cities():
        """Initialize with default cities if table is empty."""
        cities = PredefinedCitiesManager.get_all_cities(active_only=False)
        
        if len(cities) == 0:
            default_cities = [
                # Global Cities
                ("New York", "USA", 40.7128, -74.0060, "North America", "Major US city - East Coast"),
                ("London", "UK", 51.5074, -0.1278, "Europe", "Major European city"),
                ("Tokyo", "Japan", 35.6762, 139.6503, "Asia", "Major Asian city - East"),
                ("Dubai", "UAE", 25.2048, 55.2708, "Middle East", "Desert climate - Gulf region"),
                ("Sydney", "Australia", -33.8688, 151.2093, "Oceania", "Southern Hemisphere - Australia"),
                # Indian Cities
                ("Delhi", "India", 28.7041, 77.1025, "North India", "Capital city - National hub"),
                ("Mumbai", "India", 19.0760, 72.8777, "West India", "Financial hub - Gateway to India"),
                ("Bangalore", "India", 12.9716, 77.5946, "South India", "Tech hub - IT capital"),
                ("Chennai", "India", 13.0827, 80.2707, "South India", "Port city - Major metro"),
                ("Kolkata", "India", 22.5726, 88.3639, "East India", "Cultural hub - East Coast"),
            ]
            
            for city_data in default_cities:
                PredefinedCitiesManager.add_city(*city_data)
            
            print(f"✓ Initialized {len(default_cities)} predefined cities (5 global + 5 Indian)")
            return len(default_cities)
        
        return 0
