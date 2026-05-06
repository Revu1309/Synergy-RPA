"""Weather locations management model."""

from database.connection import create_connection, get_cursor, is_postgres

class WeatherLocationsManager:
    """Manage weather monitoring locations."""

    @staticmethod
    def create_table():
        """Create weather_locations table if it doesn't exist."""
        connection = create_connection()
        if connection:
            cursor = get_cursor(connection)
            if is_postgres(connection):
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
            connection.commit()
            cursor.close()
            connection.close()

    @staticmethod
    def add_location(location_name, country, latitude, longitude, notes=None):
        """Add a new weather location."""
        connection = create_connection()
        if connection:
            cursor = get_cursor(connection)
            try:
                query = """
                    INSERT INTO weather_locations 
                    (location_name, country, latitude, longitude, notes)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(query, (location_name, country, latitude, longitude, notes))
                connection.commit()
                result = True
            except Exception as e:
                print(f"Error adding location: {e}")
                result = False
            finally:
                cursor.close()
                connection.close()
            return result
        return False

    @staticmethod
    def get_all_locations(active_only=True):
        """Get all weather locations."""
        connection = create_connection()
        if connection:
            cursor = get_cursor(connection)
            if active_only:
                query = "SELECT * FROM weather_locations WHERE is_active = TRUE ORDER BY location_name"
                cursor.execute(query)
            else:
                query = "SELECT * FROM weather_locations ORDER BY location_name"
                cursor.execute(query)
            
            results = cursor.fetchall()
            cursor.close()
            connection.close()
            
            locations = []
            if results:
                for row in results:
                    locations.append({
                        'id': row[0],
                        'location_name': row[1],
                        'country': row[2],
                        'latitude': float(row[3]),
                        'longitude': float(row[4]),
                        'is_active': bool(row[5]),
                        'created_at': str(row[6]),
                        'updated_at': str(row[7]),
                        'notes': row[8]
                    })
            return locations
        return []

    @staticmethod
    def get_location(location_id):
        """Get a specific location by ID."""
        connection = create_connection()
        if connection:
            cursor = get_cursor(connection)
            query = "SELECT * FROM weather_locations WHERE id = %s"
            cursor.execute(query, (location_id,))
            result = cursor.fetchone()
            cursor.close()
            connection.close()
            
            if result:
                return {
                    'id': result[0],
                    'location_name': result[1],
                    'country': result[2],
                    'latitude': float(result[3]),
                    'longitude': float(result[4]),
                    'is_active': bool(result[5]),
                    'created_at': str(result[6]),
                    'updated_at': str(result[7]),
                    'notes': result[8]
                }
        return None

    @staticmethod
    def update_location(location_id, location_name=None, country=None, 
                       latitude=None, longitude=None, is_active=None, notes=None):
        """Update a location."""
        connection = create_connection()
        if connection:
            cursor = get_cursor(connection)
            
            # Build dynamic update query
            updates = []
            params = []
            
            if location_name is not None:
                updates.append("location_name = %s")
                params.append(location_name)
            if country is not None:
                updates.append("country = %s")
                params.append(country)
            if latitude is not None:
                updates.append("latitude = %s")
                params.append(latitude)
            if longitude is not None:
                updates.append("longitude = %s")
                params.append(longitude)
            if is_active is not None:
                updates.append("is_active = %s")
                params.append(is_active)
            if notes is not None:
                updates.append("notes = %s")
                params.append(notes)
            
            if not updates:
                return False
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(location_id)
            
            query = f"UPDATE weather_locations SET {', '.join(updates)} WHERE id = %s"
            
            try:
                cursor.execute(query, params)
                connection.commit()
                result = True
            except Exception as e:
                print(f"Error updating location: {e}")
                result = False
            finally:
                cursor.close()
                connection.close()
            return result
        return False

    @staticmethod
    def delete_location(location_id):
        """Delete a location (soft delete via is_active)."""
        connection = create_connection()
        if connection:
            cursor = get_cursor(connection)
            query = "UPDATE weather_locations SET is_active = FALSE WHERE id = %s"
            try:
                cursor.execute(query, (location_id,))
                connection.commit()
                result = True
            except Exception as e:
                print(f"Error deleting location: {e}")
                result = False
            finally:
                cursor.close()
                connection.close()
            return result
        return False

    @staticmethod
    def clear_weather_locations():
        """Clear all weather locations (for reinitializing)."""
        connection = create_connection()
        if connection:
            cursor = get_cursor(connection)
            try:
                # Delete all weather locations
                query = "DELETE FROM weather_locations"
                cursor.execute(query)
                connection.commit()
                print("✓ Cleared all weather locations")
                return True
            except Exception as e:
                print(f"Error clearing weather locations: {e}")
                return False
            finally:
                cursor.close()
                connection.close()
        return False

    @staticmethod
    def initialize_default_locations():
        """Initialize weather locations from predefined cities table."""
        from database.predefined_cities import PredefinedCitiesManager
        
        # Get predefined cities
        predefined_cities = PredefinedCitiesManager.get_all_cities(active_only=False)
        
        if predefined_cities:
            for city in predefined_cities:
                WeatherLocationsManager.add_location(
                    location_name=city['city_name'],
                    country=city['country'],
                    latitude=city['latitude'],
                    longitude=city['longitude'],
                    notes=city['description']
                )
            
            print(f"✓ Initialized {len(predefined_cities)} weather locations from predefined cities")
        else:
            print("⚠ No predefined cities found to initialize weather locations")
