import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from database.connection import create_connection

class CryptoAnalyzer:
    """Class for analyzing cryptocurrency data."""

    def __init__(self):
        pass

    def get_recent_data(self, hours=24):
        """Get recent cryptocurrency data."""
        return self.get_data_as_dataframe(hours_back=hours)

    def get_data_as_dataframe(self, symbol=None, hours_back=24):
        """Get data as pandas DataFrame."""
        conn = create_connection()
        if not conn:
            return None

        try:
            query = """
                SELECT * FROM crypto_assets
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
            """
            params = [hours_back]

            if symbol:
                query += " AND symbol = %s"
                params.append(symbol.upper())

            query += " ORDER BY timestamp DESC"

            df = pd.read_sql(query, conn, params=params)
            return df
        finally:
            conn.close()

    def get_recent_data(self, hours=24):
        """Get recent cryptocurrency data."""
        return self.get_data_as_dataframe(hours_back=hours)

    def calculate_price_changes(self, symbol, hours_back=24):
        """Calculate price changes for a specific cryptocurrency."""
        df = self.get_data_as_dataframe(symbol, hours_back)
        if df.empty:
            return None

        df = df.sort_values('timestamp')
        df['price_change_pct'] = df['price_usd'].pct_change() * 100
        df['price_change_usd'] = df['price_usd'].diff()

        return df

    def get_top_performers(self, hours_back=24, top_n=5):
        """Get top performing cryptocurrencies by price change."""
        df = self.get_data_as_dataframe(hours_back=hours_back)
        if df.empty:
            return None

        # Get latest and oldest prices for each symbol
        latest_prices = df.groupby('symbol').first().reset_index()
        oldest_prices = df.groupby('symbol').last().reset_index()

        # Calculate percentage change
        merged = pd.merge(latest_prices, oldest_prices, on='symbol', suffixes=('_latest', '_oldest'))
        merged['price_change_pct'] = ((merged['price_usd_latest'] - merged['price_usd_oldest']) / merged['price_usd_oldest']) * 100

        return merged.nlargest(top_n, 'price_change_pct')[['symbol', 'name_latest', 'price_usd_latest', 'price_change_pct']]

    def calculate_volatility(self, symbol, hours_back=24):
        """Calculate price volatility (standard deviation of returns)."""
        df = self.calculate_price_changes(symbol, hours_back)
        if df is None or df.empty:
            return None

        volatility = df['price_change_pct'].std()
        return volatility

    def get_market_summary(self, hours_back=24):
        """Get market summary statistics."""
        df = self.get_data_as_dataframe(hours_back=hours_back)
        if df.empty:
            return None

        summary = {
            'total_market_cap': df.groupby('symbol').first()['market_cap'].sum(),
            'total_volume': df.groupby('symbol').first()['volume_24h'].sum(),
            'avg_price': df['price_usd'].mean(),
            'price_std': df['price_usd'].std(),
            'unique_cryptos': df['symbol'].nunique(),
            'data_points': len(df)
        }

        return summary

    def calculate_metrics(self, df):
        """Calculate key metrics from dataframe."""
        if df.empty:
            return {}

        latest = df.sort_values('timestamp').groupby('symbol').last()
        previous = df.sort_values('timestamp').groupby('symbol').first()

        metrics = {
            'total_cryptocurrencies': int(df['symbol'].nunique()),
            'total_market_cap': float(latest['market_cap'].sum()),
            'total_volume_24h': float(latest['volume_24h'].sum()),
            'avg_price': float(latest['price_usd'].mean()),
            'price_volatility': float(latest['price_usd'].std()),
            'data_points': int(len(df))
        }

        return metrics

    def get_price_alerts(self, df, threshold_pct=5):
        """Get price alerts from dataframe."""
        if df.empty:
            return []

        alerts = []
        for symbol in df['symbol'].unique():
            symbol_df = df[df['symbol'] == symbol].sort_values('timestamp')
            if len(symbol_df) < 2:
                continue

            latest_price = symbol_df.iloc[-1]['price_usd']
            prev_price = symbol_df.iloc[-2]['price_usd']
            change_pct = ((latest_price - prev_price) / prev_price) * 100

            if abs(change_pct) >= threshold_pct:
                severity = 'high' if abs(change_pct) >= 10 else 'medium' if abs(change_pct) >= 5 else 'low'
                alerts.append({
                    'symbol': symbol,
                    'message': f"Price {'increased' if change_pct > 0 else 'decreased'} by {abs(change_pct):.2f}%",
                    'severity': severity,
                    'timestamp': symbol_df.iloc[-1]['timestamp']
                })

        return alerts

    def detect_price_alerts(self, symbol, threshold_pct=5):
        """Detect significant price changes."""
        df = self.calculate_price_changes(symbol, hours_back=1)
        if df is None or df.empty:
            return None

        alerts = []
        for _, row in df.iterrows():
            if abs(row['price_change_pct']) >= threshold_pct:
                alerts.append({
                    'symbol': symbol,
                    'timestamp': row['timestamp'],
                    'price': row['price_usd'],
                    'change_pct': row['price_change_pct'],
                    'change_type': 'increase' if row['price_change_pct'] > 0 else 'decrease'
                })

        return alerts

    def get_metrics(self):
        """Get dashboard metrics."""
        try:
            df = self.get_data_as_dataframe(hours_back=24)
            if df.empty:
                return {}
            
            latest = df.sort_values('timestamp').groupby('symbol').last()
            
            return {
                'Total Assets': str(df['symbol'].nunique()),
                'Market Cap': f"${latest['market_cap'].sum()/1e9:.2f}B",
                'Total Volume': f"${latest['volume_24h'].sum()/1e9:.2f}B",
                'Avg Price': f"${latest['price_usd'].mean():.2f}"
            }
        except Exception as e:
            print(f"Error getting metrics: {e}")
            return {}

    def get_alerts(self):
        """Get system alerts."""
        try:
            df = self.get_data_as_dataframe(hours_back=1)
            if df.empty:
                return []
            
            alerts = []
            for symbol in df['symbol'].unique():
                symbol_df = df[df['symbol'] == symbol].sort_values('timestamp')
                if len(symbol_df) < 2:
                    continue
                
                latest = symbol_df.iloc[-1]['price_usd']
                oldest = symbol_df.iloc[0]['price_usd']
                change_pct = ((latest - oldest) / oldest) * 100
                
                if abs(change_pct) > 5:
                    level = 'high' if abs(change_pct) > 10 else 'medium'
                    alerts.append({
                        'level': level,
                        'message': f"{symbol}: {change_pct:+.2f}% ({latest:.6f})"
                    })
            
            return alerts
        except Exception as e:
            print(f"Error getting alerts: {e}")
            return []

    def get_advanced_analytics(self):
        """Get advanced analytics data."""
        try:
            df = self.get_data_as_dataframe(hours_back=24)
            if df.empty:
                return {}
            
            latest = df.sort_values('timestamp').groupby('symbol').last()
            
            # Calculate 24h price change
            oldest = df.sort_values('timestamp').groupby('symbol').first()
            price_changes = ((latest['price_usd'] - oldest['price_usd']) / oldest['price_usd'] * 100).mean()
            
            return {
                'Market Cap': {
                    'value': f"${latest['market_cap'].sum()/1e9:.1f}B",
                    'icon': '💰'
                },
                '24h Volume': {
                    'value': f"${latest['volume_24h'].sum()/1e9:.1f}B",
                    'icon': '📊'
                },
                'Assets': {
                    'value': str(df['symbol'].nunique()),
                    'icon': '📈'
                },
                '24h Change': {
                    'value': f"{price_changes:+.2f}%",
                    'icon': '⚡'
                }
            }
        except Exception as e:
            print(f"Error getting advanced analytics: {e}")
            return {}

    def get_market_insights(self):
        """Get market insights."""
        try:
            df = self.get_data_as_dataframe(hours_back=24)
            if df.empty:
                return []
            
            insights = []
            
            # Top performers
            latest = df.sort_values('timestamp').groupby('symbol').last()
            oldest = df.sort_values('timestamp').groupby('symbol').first()
            changes = ((latest['price_usd'] - oldest['price_usd']) / oldest['price_usd'] * 100)
            top_3 = changes.nlargest(3)
            
            for symbol, change in top_3.items():
                insights.append({
                    'title': f'🚀 {symbol} - Top Performer',
                    'description': f'Up {change:.2f}% in the last 24 hours'
                })
            
            # Market volatility
            volatility = df['price_usd'].std()
            if volatility > df['price_usd'].mean() * 0.1:
                insights.append({
                    'title': '⚠️ High Volatility Alert',
                    'description': 'Market showing elevated price volatility patterns'
                })
            else:
                insights.append({
                    'title': '✓ Stable Market',
                    'description': 'Market conditions remain relatively stable'
                })
            
            # Trading volume
            avg_volume = df['volume_24h'].mean()
            latest_volume = df.sort_values('timestamp').iloc[0]['volume_24h']
            
            if latest_volume > avg_volume * 1.2:
                insights.append({
                    'title': '📈 High Trading Activity',
                    'description': f'Trading volume 20%+ above 24h average'
                })
            
            return insights
        except Exception as e:
            print(f"Error getting insights: {e}")
            return []

    def __del__(self):
        try:
            if self.conn:
                self.conn.close()
        except Exception:
            pass  # Ignore errors during cleanup