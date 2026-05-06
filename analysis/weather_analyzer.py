"""Weather data analyzer."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from database.connection import create_connection


class WeatherAnalyzer:
    """Class for analyzing weather data."""

    def __init__(self):
        pass

    def get_recent_data(self, hours=24, location=None):
        """Get recent weather data."""
        return self.get_data_as_dataframe(hours_back=hours, location=location)

    def get_data_as_dataframe(self, location=None, hours_back=24):
        """Get data as pandas DataFrame."""
        conn = create_connection()
        if not conn:
            return pd.DataFrame()

        query = """
            SELECT * FROM weather_data
            WHERE timestamp >= NOW() - (INTERVAL '1 hour' * %s)
        """
        params = [hours_back]

        if location:
            query += " AND location_name = %s"
            params.append(location)

        query += " ORDER BY timestamp DESC"

        try:
            df = pd.read_sql(query, conn, params=params)
            return df
        except Exception as e:
            print(f"Error reading weather data: {e}")
            return pd.DataFrame()
        finally:
            conn.close()

    def get_latest_weather_by_location(self):
        """Get latest weather data for all locations."""
        conn = create_connection()
        if not conn:
            return pd.DataFrame()

        query = """
            SELECT w1.* FROM weather_data w1
            INNER JOIN (
                SELECT location_name, MAX(timestamp) as max_timestamp
                FROM weather_data
                GROUP BY location_name
            ) w2
            ON w1.location_name = w2.location_name AND w1.timestamp = w2.max_timestamp
            ORDER BY w1.location_name
        """

        try:
            df = pd.read_sql(query, conn)
            return df
        except Exception as e:
            print(f"Error reading latest weather: {e}")
            return pd.DataFrame()
        finally:
            conn.close()

    def get_location_history(self, location, days=7):
        """Get weather history for a specific location."""
        conn = create_connection()
        if not conn:
            return pd.DataFrame()

        query = """
            SELECT * FROM weather_data
            WHERE location_name = %s
            AND timestamp >= NOW() - (INTERVAL '1 day' * %s)
            ORDER BY timestamp DESC
        """

        try:
            df = pd.read_sql(query, conn, params=[location, days])
            return df
        except Exception as e:
            print(f"Error reading location history: {e}")
            return pd.DataFrame()
        finally:
            conn.close()

    def calculate_temperature_stats(self, location=None, days=7):
        """Calculate temperature statistics."""
        if location:
            df = self.get_location_history(location, days)
        else:
            df = self.get_recent_data(hours=24*days)

        if df.empty:
            return None

        stats = {
            'avg_temp': df['temperature'].mean(),
            'min_temp': df['temperature'].min(),
            'max_temp': df['temperature'].max(),
            'std_temp': df['temperature'].std(),
            'current_temp': df.iloc[0]['temperature'] if not df.empty else None
        }

        return stats

    def calculate_humidity_stats(self, location=None, days=7):
        """Calculate humidity statistics."""
        if location:
            df = self.get_location_history(location, days)
        else:
            df = self.get_recent_data(hours=24*days)

        if df.empty:
            return None

        stats = {
            'avg_humidity': df['humidity'].mean(),
            'min_humidity': df['humidity'].min(),
            'max_humidity': df['humidity'].max(),
            'current_humidity': df.iloc[0]['humidity'] if not df.empty else None
        }

        return stats

    def get_weather_summary(self, location=None):
        """Get weather summary."""
        if location:
            df = self.get_location_history(location, 1)
        else:
            df = self.get_latest_weather_by_location()

        if df.empty:
            return None

        summary = {
            'total_locations': df['location_name'].nunique() if not location else 1,
            'avg_temperature': df['temperature'].mean(),
            'avg_humidity': df['humidity'].mean(),
            'avg_wind_speed': df['wind_speed'].mean(),
            'most_common_weather': df['weather_main'].mode()[0] if not df.empty else None,
            'data_points': len(df)
        }

        return summary

    def get_extreme_conditions(self, threshold_temp_high=30, threshold_temp_low=0, 
                              threshold_humidity=90, threshold_wind=20):
        """Get locations with extreme weather conditions."""
        df = self.get_latest_weather_by_location()

        if df.empty:
            return {}

        extremes = {
            'high_temp': df[df['temperature'] >= threshold_temp_high][['location_name', 'temperature', 'country']].to_dict('records'),
            'low_temp': df[df['temperature'] <= threshold_temp_low][['location_name', 'temperature', 'country']].to_dict('records'),
            'high_humidity': df[df['humidity'] >= threshold_humidity][['location_name', 'humidity', 'country']].to_dict('records'),
            'high_wind': df[df['wind_speed'] >= threshold_wind][['location_name', 'wind_speed', 'country']].to_dict('records'),
        }

        return extremes

    def get_weather_trends(self, location, days=7):
        """Get temperature and humidity trends for a location."""
        df = self.get_location_history(location, days)

        if df.empty:
            return None

        df = df.sort_values('timestamp')
        df['date'] = pd.to_datetime(df['timestamp']).dt.date

        trends = {
            'dates': df['date'].unique().tolist(),
            'avg_temps': df.groupby('date')['temperature'].mean().tolist(),
            'avg_humidity': df.groupby('date')['humidity'].mean().tolist(),
            'max_temps': df.groupby('date')['temperature'].max().tolist(),
            'min_temps': df.groupby('date')['temperature'].min().tolist(),
        }

        return trends

    def compare_locations(self):
        """Compare weather across all locations."""
        df = self.get_latest_weather_by_location()

        if df.empty:
            return None

        comparison = df[['location_name', 'country', 'temperature', 'humidity', 
                        'weather_main', 'wind_speed']].sort_values('temperature', ascending=False)

        return comparison.to_dict('records')
