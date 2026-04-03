"""Weather data visualization module - completely separate from crypto."""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from analysis.weather_analyzer import WeatherAnalyzer


class WeatherVisualizer:
    """Class for creating weather data visualizations."""

    def __init__(self):
        self.analyzer = WeatherAnalyzer()

    def get_current_weather_cards(self):
        """Get current weather for all locations as card data."""
        df = self.analyzer.get_latest_weather_by_location()
        
        if df.empty:
            return []
        
        cards = []
        for _, row in df.iterrows():
            card = {
                'location': row['location_name'],
                'country': row['country'],
                'temperature': round(float(row['temperature']), 1) if pd.notna(row['temperature']) else 'N/A',
                'feels_like': round(float(row['feels_like']), 1) if pd.notna(row['feels_like']) else 'N/A',
                'humidity': int(row['humidity']) if pd.notna(row['humidity']) else 'N/A',
                'weather': row['weather_main'],
                'description': row['weather_description'],
                'wind_speed': round(float(row['wind_speed']), 1) if pd.notna(row['wind_speed']) else 'N/A',
                'pressure': int(row['pressure']) if pd.notna(row['pressure']) else 'N/A',
                'cloudiness': int(row['cloudiness']) if pd.notna(row['cloudiness']) else 'N/A',
            }
            cards.append(card)
        
        return cards

    def create_temperature_comparison_chart(self):
        """Create horizontal bar chart comparing current temperatures."""
        df = self.analyzer.get_latest_weather_by_location()
        
        if df.empty:
            return None
        
        df_sorted = df.sort_values('temperature', ascending=True)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=df_sorted['location_name'],
            x=df_sorted['temperature'],
            orientation='h',
            marker=dict(
                color=df_sorted['temperature'],
                colorscale='RdYlBu_r',
                showscale=True,
                colorbar=dict(title="Temp (°C)")
            ),
            text=df_sorted['temperature'].round(1),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Temperature: %{x:.1f}°C<extra></extra>'
        ))
        
        fig.update_layout(
            title='Temperature Comparison Across Locations',
            xaxis_title='Temperature (°C)',
            yaxis_title='Location',
            height=400,
            margin=dict(l=150, r=50, t=50, b=50),
            hovermode='closest',
            plot_bgcolor='rgba(240, 240, 240, 0.5)',
        )
        
        return fig.to_html(div_id="temp_comparison_chart", include_plotlyjs=False)

    def create_humidity_comparison_chart(self):
        """Create humidity comparison chart."""
        df = self.analyzer.get_latest_weather_by_location()
        
        if df.empty:
            return None
        
        df_sorted = df.sort_values('humidity', ascending=False)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df_sorted['location_name'],
            y=df_sorted['humidity'],
            marker=dict(
                color=df_sorted['humidity'],
                colorscale='Blues',
                showscale=True,
                colorbar=dict(title="Humidity %")
            ),
            text=df_sorted['humidity'],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Humidity: %{y}%<extra></extra>'
        ))
        
        fig.update_layout(
            title='Humidity Levels Across Locations',
            yaxis_title='Humidity (%)',
            height=400,
            margin=dict(l=50, r=50, t=50, b=80),
            hovermode='x',
            plot_bgcolor='rgba(240, 240, 240, 0.5)',
        )
        
        return fig.to_html(div_id="humidity_chart", include_plotlyjs=False)

    def create_wind_speed_chart(self):
        """Create wind speed comparison chart."""
        df = self.analyzer.get_latest_weather_by_location()
        
        if df.empty:
            return None
        
        df_sorted = df.sort_values('wind_speed', ascending=False)
        
        colors = ['red' if speed > 15 else 'orange' if speed > 10 else 'green' 
                  for speed in df_sorted['wind_speed']]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df_sorted['location_name'],
            y=df_sorted['wind_speed'],
            marker=dict(color=colors),
            text=df_sorted['wind_speed'].round(1),
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Wind Speed: %{y:.1f} m/s<extra></extra>'
        ))
        
        fig.update_layout(
            title='Wind Speed Comparison (Red: Strong, Orange: Moderate, Green: Light)',
            yaxis_title='Wind Speed (m/s)',
            height=400,
            margin=dict(l=50, r=50, t=80, b=80),
            hovermode='x',
            plot_bgcolor='rgba(240, 240, 240, 0.5)',
        )
        
        return fig.to_html(div_id="wind_chart", include_plotlyjs=False)

    def create_weather_distribution_chart(self):
        """Create pie chart showing weather distribution."""
        df = self.analyzer.get_latest_weather_by_location()
        
        if df.empty:
            return None
        
        weather_counts = df['weather_main'].value_counts()
        
        fig = go.Figure(data=[go.Pie(
            labels=weather_counts.index,
            values=weather_counts.values,
            hovertemplate='<b>%{label}</b><br>Count: %{value}<extra></extra>'
        )])
        
        fig.update_layout(
            title='Weather Conditions Distribution',
            height=400,
        )
        
        return fig.to_html(div_id="weather_dist_chart", include_plotlyjs=False)

    def create_location_temperature_trend(self, location, days=7):
        """Create temperature trend chart for a specific location."""
        df = self.analyzer.get_location_history(location, days)
        
        if df.empty:
            return None
        
        df = df.sort_values('timestamp')
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['temperature'],
            mode='lines+markers',
            name='Temperature',
            line=dict(color='#FF6B6B', width=2),
            fill='tozeroy',
            hovertemplate='<b>%{x}</b><br>Temp: %{y:.1f}°C<extra></extra>'
        ))
        
        fig.update_layout(
            title=f'{location} - Temperature Trend (Last {days} Days)',
            xaxis_title='Date & Time',
            yaxis_title='Temperature (°C)',
            height=400,
            hovermode='x unified',
            plot_bgcolor='rgba(240, 240, 240, 0.5)',
        )
        
        return fig.to_html(div_id="temp_trend_chart", include_plotlyjs=False)

    def create_location_humidity_trend(self, location, days=7):
        """Create humidity trend chart for a specific location."""
        df = self.analyzer.get_location_history(location, days)
        
        if df.empty:
            return None
        
        df = df.sort_values('timestamp')
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['humidity'],
            mode='lines+markers',
            name='Humidity',
            line=dict(color='#4ECDC4', width=2),
            fill='tozeroy',
            hovertemplate='<b>%{x}</b><br>Humidity: %{y}%<extra></extra>'
        ))
        
        fig.update_layout(
            title=f'{location} - Humidity Trend (Last {days} Days)',
            xaxis_title='Date & Time',
            yaxis_title='Humidity (%)',
            height=400,
            hovermode='x unified',
            plot_bgcolor='rgba(240, 240, 240, 0.5)',
        )
        
        return fig.to_html(div_id="humidity_trend_chart", include_plotlyjs=False)

    def create_multi_parameter_chart(self, location, days=7):
        """Create multi-parameter chart (temperature, humidity, wind)."""
        df = self.analyzer.get_location_history(location, days)
        
        if df.empty:
            return None
        
        df = df.sort_values('timestamp')
        
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=('Temperature', 'Humidity', 'Wind Speed')
        )
        
        # Temperature
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['temperature'], name='Temperature',
                      line=dict(color='#FF6B6B'), hovertemplate='<b>%{x}</b><br>%{y:.1f}°C<extra></extra>'),
            row=1, col=1
        )
        
        # Humidity
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['humidity'], name='Humidity',
                      line=dict(color='#4ECDC4'), hovertemplate='<b>%{x}</b><br>%{y}%<extra></extra>'),
            row=2, col=1
        )
        
        # Wind Speed
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['wind_speed'], name='Wind Speed',
                      line=dict(color='#95E1D3'), hovertemplate='<b>%{x}</b><br>%{y:.1f} m/s<extra></extra>'),
            row=3, col=1
        )
        
        fig.update_yaxes(title_text='Temp (°C)', row=1, col=1)
        fig.update_yaxes(title_text='Humidity (%)', row=2, col=1)
        fig.update_yaxes(title_text='Wind (m/s)', row=3, col=1)
        fig.update_xaxes(title_text='Date & Time', row=3, col=1)
        
        fig.update_layout(
            title=f'{location} - Weather Parameters (Last {days} Days)',
            height=700,
            hovermode='x unified',
            plot_bgcolor='rgba(240, 240, 240, 0.5)',
        )
        
        return fig.to_html(div_id="multi_param_chart", include_plotlyjs=False)

    def create_extreme_conditions_alert(self):
        """Create a summary of extreme weather conditions."""
        extremes = self.analyzer.get_extreme_conditions()
        
        alert_html = '<div class="extreme-conditions-summary">'
        
        if extremes.get('high_temp'):
            alert_html += '<div class="alert alert-danger"><strong>🔥 High Temperature:</strong><br>'
            for item in extremes['high_temp']:
                alert_html += f"{item['location_name']} ({item['country']}): {item['temperature']:.1f}°C<br>"
            alert_html += '</div>'
        
        if extremes.get('high_humidity'):
            alert_html += '<div class="alert alert-info"><strong>💧 High Humidity:</strong><br>'
            for item in extremes['high_humidity']:
                alert_html += f"{item['location_name']} ({item['country']}): {item['humidity']}%<br>"
            alert_html += '</div>'
        
        if extremes.get('high_wind'):
            alert_html += '<div class="alert alert-warning"><strong>💨 Strong Wind:</strong><br>'
            for item in extremes['high_wind']:
                alert_html += f"{item['location_name']} ({item['country']}): {item['wind_speed']:.1f} m/s<br>"
            alert_html += '</div>'
        
        alert_html += '</div>'
        
        return alert_html if len(extremes['high_temp'] or extremes['high_humidity'] or extremes['high_wind']) > 0 else ''

    def get_weather_summary_stats(self):
        """Get summary statistics for weather dashboard."""
        summary = self.analyzer.get_weather_summary()
        
        if summary is None:
            return {}
        
        return {
            'total_locations': summary.get('total_locations', 0),
            'avg_temperature': round(float(summary.get('avg_temperature', 0)), 1),
            'avg_humidity': round(float(summary.get('avg_humidity', 0)), 1),
            'avg_wind_speed': round(float(summary.get('avg_wind_speed', 0)), 1),
            'common_weather': summary.get('most_common_weather', 'N/A'),
        }
