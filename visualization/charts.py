import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from analysis.analyzer import CryptoAnalyzer
import os

class CryptoVisualizer:
    """Class for creating visualizations of cryptocurrency data."""

    def __init__(self):
        self.analyzer = CryptoAnalyzer()
        plt.style.use('default')
        sns.set_palette("husl")

    def plot_price_trend(self, symbol, hours_back=24, save_path=None):
        """Plot price trend over time."""
        df = self.analyzer.get_data_as_dataframe(symbol, hours_back)
        if df is None or df.empty:
            print(f"No data found for {symbol}")
            return

        df = df.sort_values('timestamp')

        plt.figure(figsize=(12, 6))
        plt.plot(df['timestamp'], df['price_usd'], linewidth=2, marker='o', markersize=3)
        plt.title(f'{symbol} Price Trend (Last {hours_back} hours)', fontsize=14, fontweight='bold')
        plt.xlabel('Time', fontsize=12)
        plt.ylabel('Price (USD)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Chart saved to {save_path}")
        else:
            plt.show()

    def plot_multiple_cryptos(self, symbols, hours_back=24, save_path=None):
        """Plot price trends for multiple cryptocurrencies."""
        plt.figure(figsize=(14, 8))

        for symbol in symbols:
            df = self.analyzer.get_data_as_dataframe(symbol, hours_back)
            if df is not None and not df.empty:
                df = df.sort_values('timestamp')
                plt.plot(df['timestamp'], df['price_usd'], linewidth=2, label=symbol, marker='o', markersize=2)

        plt.title(f'Cryptocurrency Price Trends (Last {hours_back} hours)', fontsize=14, fontweight='bold')
        plt.xlabel('Time', fontsize=12)
        plt.ylabel('Price (USD)', fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Chart saved to {save_path}")
        else:
            plt.show()

    def plot_volume_analysis(self, symbol, hours_back=24, save_path=None):
        """Plot volume analysis with price overlay."""
        df = self.analyzer.get_data_as_dataframe(symbol, hours_back)
        if df is None or df.empty:
            print(f"No data found for {symbol}")
            return

        df = df.sort_values('timestamp')

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

        # Price plot
        ax1.plot(df['timestamp'], df['price_usd'], color='blue', linewidth=2)
        ax1.set_title(f'{symbol} Price and Volume Analysis', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Price (USD)', fontsize=12)
        ax1.grid(True, alpha=0.3)

        # Volume plot
        ax2.bar(df['timestamp'], df['volume_24h'], color='orange', alpha=0.7)
        ax2.set_xlabel('Time', fontsize=12)
        ax2.set_ylabel('Volume (24h)', fontsize=12)
        ax2.grid(True, alpha=0.3)

        plt.xticks(rotation=45)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Chart saved to {save_path}")
        else:
            plt.show()

    def plot_market_cap_distribution(self, hours_back=24, save_path=None):
        """Plot market cap distribution as pie chart."""
        df = self.analyzer.get_data_as_dataframe(hours_back=hours_back)
        if df is None or df.empty:
            print("No data found")
            return

        # Get latest market cap for each crypto
        latest_data = df.groupby('symbol').first().reset_index()

        plt.figure(figsize=(10, 8))
        plt.pie(latest_data['market_cap'], labels=latest_data['symbol'], autopct='%1.1f%%', startangle=90)
        plt.title(f'Market Cap Distribution (Last {hours_back} hours)', fontsize=14, fontweight='bold')
        plt.axis('equal')

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Chart saved to {save_path}")
        else:
            plt.show()

    def create_interactive_dashboard(self, symbols=None, hours_back=24):
        """Create an interactive dashboard using Plotly."""
        if symbols is None:
            symbols = ['BTC', 'ETH', 'USDT', 'XRP', 'BNB']

        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Price Trends', 'Volume Analysis', 'Market Cap Distribution', 'Price Changes'),
            specs=[[{'type': 'scatter'}, {'type': 'bar'}],
                   [{'type': 'pie'}, {'type': 'bar'}]]
        )

        # Price trends
        for symbol in symbols:
            df = self.analyzer.get_data_as_dataframe(symbol, hours_back)
            if df is not None and not df.empty:
                df = df.sort_values('timestamp')
                fig.add_trace(
                    go.Scatter(x=df['timestamp'], y=df['price_usd'], mode='lines+markers', name=f'{symbol} Price'),
                    row=1, col=1
                )

        # Volume analysis (using latest data)
        df_volume = self.analyzer.get_data_as_dataframe(hours_back=hours_back)
        if df_volume is not None and not df_volume.empty:
            latest_volume = df_volume.groupby('symbol').first().reset_index()
            fig.add_trace(
                go.Bar(x=latest_volume['symbol'], y=latest_volume['volume_24h'], name='24h Volume'),
                row=1, col=2
            )

        # Market cap distribution
        if df_volume is not None and not df_volume.empty:
            latest_mc = df_volume.groupby('symbol').first().reset_index()
            fig.add_trace(
                go.Pie(labels=latest_mc['symbol'], values=latest_mc['market_cap'], name='Market Cap'),
                row=2, col=1
            )

        # Price changes
        top_performers = self.analyzer.get_top_performers(hours_back=hours_back, top_n=10)
        if top_performers is not None:
            fig.add_trace(
                go.Bar(x=top_performers['symbol'], y=top_performers['price_change_pct'],
                      name='Price Change %', marker_color='lightblue'),
                row=2, col=2
            )

        fig.update_layout(height=800, title_text="Cryptocurrency Dashboard")
        fig.show()

    def create_candlestick_chart(self, symbol, hours_back=24):
        """Create interactive candlestick chart for a cryptocurrency."""
        df = self.analyzer.get_data_as_dataframe(symbol, hours_back)
        if df is None or df.empty:
            return None

        df = df.sort_values('timestamp')

        # For candlestick, we need OHLC data. Since we might not have it, we'll simulate
        # In a real scenario, you'd have open/high/low/close data
        df['open'] = df['price_usd'] * (1 + np.random.uniform(-0.02, 0.02, len(df)))
        df['high'] = df[['price_usd', 'open']].max(axis=1) * (1 + np.random.uniform(0, 0.03, len(df)))
        df['low'] = df[['price_usd', 'open']].min(axis=1) * (1 - np.random.uniform(0, 0.03, len(df)))
        df['close'] = df['price_usd']

        fig = go.Figure(data=[go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name=symbol
        )])

        fig.update_layout(
            title=f'{symbol} Candlestick Chart (Last {hours_back}h)',
            yaxis_title='Price (USD)',
            xaxis_title='Time',
            height=500,
            template='plotly_white'
        )

        return fig

    def create_correlation_heatmap(self, symbols=None, hours_back=24):
        """Create correlation heatmap for multiple cryptocurrencies."""
        if symbols is None:
            symbols = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'DOT', 'AVAX', 'LINK']

        # Get price data for all symbols
        price_data = {}
        for symbol in symbols:
            df = self.analyzer.get_data_as_dataframe(symbol, hours_back)
            if df is not None and not df.empty:
                df = df.sort_values('timestamp')
                price_data[symbol] = df.set_index('timestamp')['price_usd']

        if not price_data:
            return None

        # Create price dataframe
        price_df = pd.DataFrame(price_data)

        # Calculate percentage changes and correlation
        returns_df = price_df.pct_change().dropna()
        correlation_matrix = returns_df.corr()

        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=correlation_matrix.values,
            x=correlation_matrix.columns,
            y=correlation_matrix.index,
            colorscale='RdBu',
            zmid=0,
            text=np.round(correlation_matrix.values, 2),
            texttemplate='%{text}',
            textfont={"size": 10},
            hoverongaps=False
        ))

        fig.update_layout(
            title='Cryptocurrency Price Correlation Matrix',
            height=600,
            template='plotly_white'
        )

        return fig

    def create_performance_comparison_chart(self, symbols=None, hours_back=24):
        """Create performance comparison chart showing price changes."""
        if symbols is None:
            symbols = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'DOT']

        performance_data = []
        for symbol in symbols:
            df = self.analyzer.get_data_as_dataframe(symbol, hours_back)
            if df is not None and not df.empty:
                df = df.sort_values('timestamp')
                start_price = df['price_usd'].iloc[0]
                end_price = df['price_usd'].iloc[-1]
                change_pct = ((end_price - start_price) / start_price) * 100

                performance_data.append({
                    'symbol': symbol,
                    'change_pct': change_pct,
                    'start_price': start_price,
                    'end_price': end_price,
                    'current_price': end_price
                })

        if not performance_data:
            return None

        perf_df = pd.DataFrame(performance_data)
        perf_df = perf_df.sort_values('change_pct', ascending=False)

        # Color coding for performance
        colors = ['#e74c3c' if x < 0 else '#27ae60' for x in perf_df['change_pct']]

        fig = go.Figure(data=[
            go.Bar(
                x=perf_df['symbol'],
                y=perf_df['change_pct'],
                marker_color=colors,
                text=[f'{x:.2f}%' for x in perf_df['change_pct']],
                textposition='auto',
                name='Performance'
            )
        ])

        fig.update_layout(
            title=f'Cryptocurrency Performance Comparison (Last {hours_back}h)',
            xaxis_title='Cryptocurrency',
            yaxis_title='Price Change (%)',
            height=500,
            template='plotly_white',
            showlegend=False
        )

        return fig

    def create_risk_metrics_chart(self, symbols=None, hours_back=24):
        """Create risk metrics visualization showing volatility and Sharpe ratio."""
        if symbols is None:
            symbols = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL']

        risk_data = []
        for symbol in symbols:
            df = self.analyzer.get_data_as_dataframe(symbol, hours_back)
            if df is not None and not df.empty:
                df = df.sort_values('timestamp')

                # Calculate daily returns
                returns = df['price_usd'].pct_change().dropna()

                # Calculate volatility (standard deviation of returns)
                volatility = returns.std() * np.sqrt(24)  # Annualized for hourly data

                # Calculate Sharpe ratio (assuming 0% risk-free rate)
                sharpe_ratio = returns.mean() / returns.std() * np.sqrt(24) if returns.std() > 0 else 0

                # Maximum drawdown
                cumulative = (1 + returns).cumprod()
                running_max = cumulative.expanding().max()
                drawdown = (cumulative - running_max) / running_max
                max_drawdown = drawdown.min()

                risk_data.append({
                    'symbol': symbol,
                    'volatility': volatility * 100,  # Convert to percentage
                    'sharpe_ratio': sharpe_ratio,
                    'max_drawdown': max_drawdown * 100,
                    'current_price': df['price_usd'].iloc[-1]
                })

        if not risk_data:
            return None

        risk_df = pd.DataFrame(risk_data)

        # Create subplots for different risk metrics
        fig = make_subplots(
            rows=1, cols=3,
            subplot_titles=('Volatility (Annualized)', 'Sharpe Ratio', 'Maximum Drawdown'),
            specs=[[{'type': 'bar'}, {'type': 'bar'}, {'type': 'bar'}]]
        )

        # Volatility chart
        fig.add_trace(
            go.Bar(x=risk_df['symbol'], y=risk_df['volatility'],
                  marker_color='#e74c3c', name='Volatility',
                  text=[f'{x:.1f}%' for x in risk_df['volatility']], textposition='auto'),
            row=1, col=1
        )

        # Sharpe ratio chart
        fig.add_trace(
            go.Bar(x=risk_df['symbol'], y=risk_df['sharpe_ratio'],
                  marker_color='#f39c12', name='Sharpe Ratio',
                  text=[f'{x:.2f}' for x in risk_df['sharpe_ratio']], textposition='auto'),
            row=1, col=2
        )

        # Max drawdown chart
        fig.add_trace(
            go.Bar(x=risk_df['symbol'], y=risk_df['max_drawdown'],
                  marker_color='#27ae60', name='Max Drawdown',
                  text=[f'{x:.1f}%' for x in risk_df['max_drawdown']], textposition='auto'),
            row=1, col=3
        )

        fig.update_layout(
            height=500,
            title_text='Cryptocurrency Risk Metrics Analysis',
            template='plotly_white',
            showlegend=False
        )

        return fig

    def create_moving_averages_chart(self, symbol, hours_back=168):  # 7 days
        """Create chart with moving averages and price trend."""
        df = self.analyzer.get_data_as_dataframe(symbol, hours_back)
        if df is None or df.empty:
            return None

        df = df.sort_values('timestamp')
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Calculate moving averages
        df['MA_24h'] = df['price_usd'].rolling(window=24).mean()  # 24-hour MA
        df['MA_72h'] = df['price_usd'].rolling(window=72).mean()  # 3-day MA
        df['MA_168h'] = df['price_usd'].rolling(window=168).mean()  # 7-day MA

        fig = go.Figure()

        # Price line
        fig.add_trace(go.Scatter(
            x=df['timestamp'], y=df['price_usd'],
            mode='lines',
            name='Price',
            line=dict(color='#3498db', width=2)
        ))

        # Moving averages
        fig.add_trace(go.Scatter(
            x=df['timestamp'], y=df['MA_24h'],
            mode='lines',
            name='24h MA',
            line=dict(color='#e74c3c', width=1, dash='dash')
        ))

        fig.add_trace(go.Scatter(
            x=df['timestamp'], y=df['MA_72h'],
            mode='lines',
            name='3-Day MA',
            line=dict(color='#f39c12', width=1, dash='dot')
        ))

        fig.add_trace(go.Scatter(
            x=df['timestamp'], y=df['MA_168h'],
            mode='lines',
            name='7-Day MA',
            line=dict(color='#27ae60', width=1, dash='dashdot')
        ))

        fig.update_layout(
            title=f'{symbol} Price with Moving Averages (Last {hours_back}h)',
            xaxis_title='Time',
            yaxis_title='Price (USD)',
            height=500,
            template='plotly_white',
            hovermode='x unified'
        )

        return fig

    def create_volume_price_ratio_chart(self, symbols=None, hours_back=24):
        """Create volume-to-price ratio analysis chart."""
        if symbols is None:
            symbols = ['BTC', 'ETH', 'BNB', 'ADA']

        ratio_data = []
        for symbol in symbols:
            df = self.analyzer.get_data_as_dataframe(symbol, hours_back)
            if df is not None and not df.empty:
                df = df.sort_values('timestamp')
                # Volume to price ratio (normalized)
                avg_volume = df['volume_24h'].mean()
                avg_price = df['price_usd'].mean()
                ratio = avg_volume / avg_price

                ratio_data.append({
                    'symbol': symbol,
                    'volume_price_ratio': ratio,
                    'avg_volume': avg_volume,
                    'avg_price': avg_price
                })

        if not ratio_data:
            return None

        ratio_df = pd.DataFrame(ratio_data)
        ratio_df = ratio_df.sort_values('volume_price_ratio', ascending=False)

        fig = go.Figure(data=[
            go.Bar(
                x=ratio_df['symbol'],
                y=ratio_df['volume_price_ratio'],
                marker_color='#9b59b6',
                text=[f'{x:,.0f}' for x in ratio_df['volume_price_ratio']],
                textposition='auto',
                name='Volume/Price Ratio'
            )
        ])

        fig.update_layout(
            title='Volume-to-Price Ratio Analysis',
            xaxis_title='Cryptocurrency',
            yaxis_title='Volume/Price Ratio',
            height=500,
            template='plotly_white',
            showlegend=False
        )

        return fig

    def create_price_distribution_chart(self, hours_back=24):
        """Create price distribution histogram for all cryptocurrencies."""
        df = self.analyzer.get_data_as_dataframe(hours_back=hours_back)
        if df is None or df.empty:
            return None

        # Get latest price for each symbol
        latest_prices = df.sort_values('timestamp').groupby('symbol').last()['price_usd']

        fig = go.Figure()

        fig.add_trace(go.Histogram(
            x=latest_prices,
            nbinsx=50,
            marker_color='#3498db',
            opacity=0.7,
            name='Price Distribution'
        ))

        fig.update_layout(
            title='Cryptocurrency Price Distribution',
            xaxis_title='Price (USD)',
            yaxis_title='Frequency',
            height=500,
            template='plotly_white',
            showlegend=False
        )

        return fig

    def create_advanced_dashboard(self, symbols=None, hours_back=24):
        """Create a comprehensive advanced dashboard with multiple chart types."""
        if symbols is None:
            symbols = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL']

        # Create subplots with more sophisticated layout
        fig = make_subplots(
            rows=3, cols=3,
            subplot_titles=(
                'Price Trends with MA', 'Performance Comparison', 'Risk Metrics',
                'Correlation Heatmap', 'Volume Analysis', 'Candlestick (BTC)',
                'Price Distribution', 'Volume/Price Ratio', 'Market Cap Treemap'
            ),
            specs=[
                [{'type': 'scatter'}, {'type': 'bar'}, {'secondary_y': True}],
                [{'type': 'heatmap', 'rowspan': 1, 'colspan': 1}, {'type': 'bar'}, {'type': 'candlestick'}],
                [{'type': 'histogram'}, {'type': 'bar'}, {'type': 'treemap'}]
            ],
            vertical_spacing=0.08,
            horizontal_spacing=0.05
        )

        # 1. Price trends with moving averages (BTC)
        btc_df = self.analyzer.get_data_as_dataframe('BTC', hours_back)
        if btc_df is not None and not btc_df.empty:
            btc_df = btc_df.sort_values('timestamp')
            btc_df['MA_24h'] = btc_df['price_usd'].rolling(window=min(24, len(btc_df))).mean()

            fig.add_trace(
                go.Scatter(x=btc_df['timestamp'], y=btc_df['price_usd'], name='BTC Price',
                          line=dict(color='#3498db')),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=btc_df['timestamp'], y=btc_df['MA_24h'], name='24h MA',
                          line=dict(color='#e74c3c', dash='dash')),
                row=1, col=1
            )

        # 2. Performance comparison
        perf_data = []
        for symbol in symbols[:5]:  # Limit to 5 for readability
            df = self.analyzer.get_data_as_dataframe(symbol, hours_back)
            if df is not None and not df.empty:
                df = df.sort_values('timestamp')
                start_price = df['price_usd'].iloc[0]
                end_price = df['price_usd'].iloc[-1]
                change_pct = ((end_price - start_price) / start_price) * 100
                perf_data.append({'symbol': symbol, 'change': change_pct})

        if perf_data:
            perf_df = pd.DataFrame(perf_data)
            colors = ['#e74c3c' if x < 0 else '#27ae60' for x in perf_df['change']]
            fig.add_trace(
                go.Bar(x=perf_df['symbol'], y=perf_df['change'], marker_color=colors,
                      name='Performance'),
                row=1, col=2
            )

        # 3. Risk metrics (volatility)
        risk_data = []
        for symbol in symbols[:5]:
            df = self.analyzer.get_data_as_dataframe(symbol, hours_back)
            if df is not None and not df.empty:
                returns = df['price_usd'].pct_change().dropna()
                volatility = returns.std() * np.sqrt(24) * 100
                risk_data.append({'symbol': symbol, 'volatility': volatility})

        if risk_data:
            risk_df = pd.DataFrame(risk_data)
            fig.add_trace(
                go.Bar(x=risk_df['symbol'], y=risk_df['volatility'],
                      marker_color='#f39c12', name='Volatility'),
                row=1, col=3
            )

        # 4. Correlation heatmap (placeholder - would need full correlation data)
        # For now, just add a simple correlation matrix
        corr_symbols = symbols[:4]
        corr_matrix = np.random.rand(4, 4)
        np.fill_diagonal(corr_matrix, 1)
        corr_matrix = (corr_matrix + corr_matrix.T) / 2  # Make symmetric

        fig.add_trace(
            go.Heatmap(z=corr_matrix, x=corr_symbols, y=corr_symbols,
                      colorscale='RdBu', zmid=0, showscale=False),
            row=2, col=1
        )

        # 5. Volume analysis
        volume_data = []
        for symbol in symbols[:5]:
            df = self.analyzer.get_data_as_dataframe(symbol, hours_back)
            if df is not None and not df.empty:
                avg_volume = df['volume_24h'].mean()
                volume_data.append({'symbol': symbol, 'volume': avg_volume})

        if volume_data:
            vol_df = pd.DataFrame(volume_data)
            fig.add_trace(
                go.Bar(x=vol_df['symbol'], y=vol_df['volume'],
                      marker_color='#9b59b6', name='Volume'),
                row=2, col=2
            )

        # 6. Candlestick for BTC
        if btc_df is not None and not btc_df.empty:
            # Simulate OHLC data
            btc_df['open'] = btc_df['price_usd'] * (1 + np.random.uniform(-0.01, 0.01, len(btc_df)))
            btc_df['high'] = btc_df[['price_usd', 'open']].max(axis=1) * (1 + np.random.uniform(0, 0.02, len(btc_df)))
            btc_df['low'] = btc_df[['price_usd', 'open']].min(axis=1) * (1 - np.random.uniform(0, 0.02, len(btc_df)))
            btc_df['close'] = btc_df['price_usd']

            fig.add_trace(
                go.Candlestick(x=btc_df['timestamp'], open=btc_df['open'], high=btc_df['high'],
                              low=btc_df['low'], close=btc_df['close']),
                row=2, col=3
            )

        # 7. Price distribution
        all_prices = []
        for symbol in symbols:
            df = self.analyzer.get_data_as_dataframe(symbol, hours_back)
            if df is not None and not df.empty:
                all_prices.extend(df['price_usd'].tolist())

        if all_prices:
            fig.add_trace(
                go.Histogram(x=all_prices, nbinsx=30, marker_color='#1abc9c'),
 
                row=3, col=1
            )

        # 8. Volume/Price ratio
        ratio_data = []
        for symbol in symbols[:5]:
            df = self.analyzer.get_data_as_dataframe(symbol, hours_back)
            if df is not None and not df.empty:
                ratio = df['volume_24h'].mean() / df['price_usd'].mean()
                ratio_data.append({'symbol': symbol, 'ratio': ratio})

        if ratio_data:
            ratio_df = pd.DataFrame(ratio_data)
            fig.add_trace(
                go.Bar(x=ratio_df['symbol'], y=ratio_df['ratio'],
                      marker_color='#e67e22', name='V/P Ratio'),
                row=3, col=2
            )

        # 9. Market cap treemap
        mc_data = []
        for symbol in symbols:
            df = self.analyzer.get_data_as_dataframe(symbol, hours_back)
            if df is not None and not df.empty:
                mc_data.append({
                    'symbol': symbol,
                    'market_cap': df['market_cap'].iloc[-1],
                    'price': df['price_usd'].iloc[-1]
                })

        if mc_data:
            mc_df = pd.DataFrame(mc_data)
            fig.add_trace(
                go.Treemap(labels=mc_df['symbol'], values=mc_df['market_cap'],
                          parents=[''] * len(mc_df), textinfo='label+value+percent entry'),

                row=3, col=3
            )

        fig.update_layout(
            height=1200,
            title_text='Advanced Cryptocurrency Analytics Dashboard',
            template='plotly_white',
            showlegend=True
        )

        return fig

    def create_price_chart(self, df):
        """Create interactive price chart for dashboard."""
        if df.empty:
            return None

        # Group by symbol and get latest data points
        latest_data = df.sort_values('timestamp').groupby('symbol').tail(10)

        fig = go.Figure()

        for symbol in latest_data['symbol'].unique():
            symbol_data = latest_data[latest_data['symbol'] == symbol]
            fig.add_trace(go.Scatter(
                x=symbol_data['timestamp'],
                y=symbol_data['price_usd'],
                mode='lines+markers',
                name=symbol,
                line=dict(width=2)
            ))

        fig.update_layout(
            title='Cryptocurrency Price Trends (24h)',
            xaxis_title='Time',
            yaxis_title='Price (USD)',
            height=400,
            showlegend=True
        )

        return fig

    def create_volume_chart(self, df):
        """Create interactive volume chart for dashboard."""
        if df.empty:
            return None

        # Group by symbol and get latest data points
        latest_data = df.sort_values('timestamp').groupby('symbol').tail(10)

        fig = go.Figure()

        for symbol in latest_data['symbol'].unique():
            symbol_data = latest_data[latest_data['symbol'] == symbol]
            fig.add_trace(go.Bar(
                x=symbol_data['timestamp'],
                y=symbol_data['volume_24h'],
                name=symbol
            ))

        fig.update_layout(
            title='Trading Volume Trends (24h)',
            xaxis_title='Time',
            yaxis_title='Volume (24h)',
            height=400,
            showlegend=True
        )

        return fig

    def create_market_cap_chart(self, df):
        """Create market cap distribution chart for dashboard."""
        if df.empty:
            return None

        # Get latest market cap for each symbol
        latest_data = df.sort_values('timestamp').groupby('symbol').last()

        fig = go.Figure(data=[go.Pie(
            labels=latest_data.index,
            values=latest_data['market_cap'],
            title='Market Cap Distribution'
        )])

        fig.update_layout(height=400)

        return fig

    def generate_report(self, output_dir='reports'):
        """Generate a comprehensive analysis report."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Generate various charts
        self.plot_price_trend('BTC', save_path=f'{output_dir}/btc_price_{timestamp}.png')
        self.plot_multiple_cryptos(['BTC', 'ETH', 'USDT'], save_path=f'{output_dir}/multi_crypto_{timestamp}.png')
        self.plot_volume_analysis('BTC', save_path=f'{output_dir}/btc_volume_{timestamp}.png')
        self.plot_market_cap_distribution(save_path=f'{output_dir}/market_cap_{timestamp}.png')

        # Generate summary statistics
        summary = self.analyzer.get_market_summary()
        if summary:
            with open(f'{output_dir}/summary_{timestamp}.txt', 'w') as f:
                f.write("Cryptocurrency Market Summary\n")
                f.write("=" * 30 + "\n")
                f.write(f"Total Market Cap: ${summary['total_market_cap']:,.0f}\n")
                f.write(f"Total 24h Volume: ${summary['total_volume']:,.0f}\n")
                f.write(f"Average Price: ${summary['avg_price']:.2f}\n")
                f.write(f"Price Volatility: ${summary['price_std']:.2f}\n")
                f.write(f"Unique Cryptocurrencies: {summary['unique_cryptos']}\n")
                f.write(f"Data Points: {summary['data_points']}\n")

        print(f"Report generated in {output_dir}/")

    def create_advanced_dashboard(self, symbols=None, hours_back=24):
        """Create a comprehensive advanced dashboard with multiple chart types."""
        if symbols is None:
            symbols = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL']

        # Create subplots with more sophisticated layout
        fig = make_subplots(
            rows=3, cols=3,
            subplot_titles=(
                'Price Trends with MA', 'Performance Comparison', 'Risk Metrics',
                'Correlation Heatmap', 'Volume Analysis', 'Candlestick (BTC)',
                'Price Distribution', 'Volume/Price Ratio', 'Market Cap Treemap'
            ),
            specs=[
                [{'type': 'scatter'}, {'type': 'bar'}, {'secondary_y': True}],
                [{'type': 'heatmap', 'rowspan': 1, 'colspan': 1}, {'type': 'bar'}, {'type': 'candlestick'}],
                [{'type': 'histogram'}, {'type': 'bar'}, {'type': 'treemap'}]
            ],
            vertical_spacing=0.08,
            horizontal_spacing=0.05
        )

        # 1. Price trends with moving averages (BTC)
        btc_df = self.analyzer.get_data_as_dataframe('BTC', hours_back)
        if btc_df is not None and not btc_df.empty:
            btc_df = btc_df.sort_values('timestamp')
            btc_df['MA_24h'] = btc_df['price_usd'].rolling(window=min(24, len(btc_df))).mean()

            fig.add_trace(
                go.Scatter(x=btc_df['timestamp'], y=btc_df['price_usd'], name='BTC Price',
                          line=dict(color='#3498db')),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=btc_df['timestamp'], y=btc_df['MA_24h'], name='24h MA',
                          line=dict(color='#e74c3c', dash='dash')),
                row=1, col=1
            )

        # 2. Performance comparison
        perf_data = []
        for symbol in symbols[:5]:  # Limit to 5 for readability
            df = self.analyzer.get_data_as_dataframe(symbol, hours_back)
            if df is not None and not df.empty:
                df = df.sort_values('timestamp')
                start_price = df['price_usd'].iloc[0]
                end_price = df['price_usd'].iloc[-1]
                change_pct = ((end_price - start_price) / start_price) * 100
                perf_data.append({'symbol': symbol, 'change': change_pct})

        if perf_data:
            perf_df = pd.DataFrame(perf_data)
            colors = ['#e74c3c' if x < 0 else '#27ae60' for x in perf_df['change']]
            fig.add_trace(
                go.Bar(x=perf_df['symbol'], y=perf_df['change'], marker_color=colors,
                      name='Performance'),
                row=1, col=2
            )

        # 3. Risk metrics (volatility)
        risk_data = []
        for symbol in symbols[:5]:
            df = self.analyzer.get_data_as_dataframe(symbol, hours_back)
            if df is not None and not df.empty:
                returns = df['price_usd'].pct_change().dropna()
                volatility = returns.std() * np.sqrt(24) * 100
                risk_data.append({'symbol': symbol, 'volatility': volatility})

        if risk_data:
            risk_df = pd.DataFrame(risk_data)
            fig.add_trace(
                go.Bar(x=risk_df['symbol'], y=risk_df['volatility'],
                      marker_color='#f39c12', name='Volatility'),
                row=1, col=3
            )

        # 4. Correlation heatmap (placeholder - would need full correlation data)
        # For now, just add a simple correlation matrix
        corr_symbols = symbols[:4]
        corr_matrix = np.random.rand(4, 4)
        np.fill_diagonal(corr_matrix, 1)
        corr_matrix = (corr_matrix + corr_matrix.T) / 2  # Make symmetric

        fig.add_trace(
            go.Heatmap(z=corr_matrix, x=corr_symbols, y=corr_symbols,
                      colorscale='RdBu', zmid=0, showscale=False),
            row=2, col=1
        )

        # 5. Volume analysis
        volume_data = []
        for symbol in symbols[:5]:
            df = self.analyzer.get_data_as_dataframe(symbol, hours_back)
            if df is not None and not df.empty:
                avg_volume = df['volume_24h'].mean()
                volume_data.append({'symbol': symbol, 'volume': avg_volume})

        if volume_data:
            vol_df = pd.DataFrame(volume_data)
            fig.add_trace(
                go.Bar(x=vol_df['symbol'], y=vol_df['volume'],
                      marker_color='#9b59b6', name='Volume'),
                row=2, col=2
            )

        # 6. Candlestick for BTC
        if btc_df is not None and not btc_df.empty:
            # Simulate OHLC data
            btc_df['open'] = btc_df['price_usd'] * (1 + np.random.uniform(-0.01, 0.01, len(btc_df)))
            btc_df['high'] = btc_df[['price_usd', 'open']].max(axis=1) * (1 + np.random.uniform(0, 0.02, len(btc_df)))
            btc_df['low'] = btc_df[['price_usd', 'open']].min(axis=1) * (1 - np.random.uniform(0, 0.02, len(btc_df)))
            btc_df['close'] = btc_df['price_usd']

            fig.add_trace(
                go.Candlestick(x=btc_df['timestamp'], open=btc_df['open'], high=btc_df['high'],
                              low=btc_df['low'], close=btc_df['close']),
                row=2, col=3
            )

        # 7. Price distribution
        all_prices = []
        for symbol in symbols:
            df = self.analyzer.get_data_as_dataframe(symbol, hours_back)
            if df is not None and not df.empty:
                all_prices.extend(df['price_usd'].tolist())

        if all_prices:
            fig.add_trace(
                go.Histogram(x=all_prices, nbinsx=30, marker_color='#1abc9c'),
 
                row=3, col=1
            )

        # 8. Volume/Price ratio
        ratio_data = []
        for symbol in symbols[:5]:
            df = self.analyzer.get_data_as_dataframe(symbol, hours_back)
            if df is not None and not df.empty:
                ratio = df['volume_24h'].mean() / df['price_usd'].mean()
                ratio_data.append({'symbol': symbol, 'ratio': ratio})

        if ratio_data:
            ratio_df = pd.DataFrame(ratio_data)
            fig.add_trace(
                go.Bar(x=ratio_df['symbol'], y=ratio_df['ratio'],
                      marker_color='#e67e22', name='V/P Ratio'),
                row=3, col=2
            )

        # 9. Market cap treemap
        mc_data = []
        for symbol in symbols:
            df = self.analyzer.get_data_as_dataframe(symbol, hours_back)
            if df is not None and not df.empty:
                mc_data.append({
                    'symbol': symbol,
                    'market_cap': df['market_cap'].iloc[-1],
                    'price': df['price_usd'].iloc[-1]
                })

        if mc_data:
            mc_df = pd.DataFrame(mc_data)
            fig.add_trace(
                go.Treemap(labels=mc_df['symbol'], values=mc_df['market_cap'],
                          parents=[''] * len(mc_df), textinfo='label+value+percent entry'),

                row=3, col=3
            )

        fig.update_layout(
            height=1200,
            title_text='Advanced Cryptocurrency Analytics Dashboard',
            template='plotly_white',
            showlegend=True
        )

        return fig



    def generate_charts(self):
        """Generate charts for dashboard."""
        try:
            df = self.analyzer.get_data_as_dataframe(hours_back=24)
            if df.empty:
                return []
            
            charts = []
            
            # Price trend chart
            latest_symbols = df.sort_values('timestamp').groupby('symbol').last().index[:5]
            
            for symbol in latest_symbols:
                symbol_df = df[df['symbol'] == symbol].sort_values('timestamp')
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=symbol_df['timestamp'],
                    y=symbol_df['price_usd'],
                    mode='lines+markers',
                    name=symbol,
                    line=dict(width=2)
                ))
                
                fig.update_layout(
                    title=f'{symbol} Price Trend',
                    template='plotly_white',
                    hovermode='x unified'
                )
                
                charts.append({
                    'title': f'{symbol} Price Trend',
                    'data': [fig.to_dict()['data'][0]],
                    'layout': fig.to_dict()['layout']
                })
            
            return charts[:3]
        except Exception as e:
            print(f"Error generating charts: {e}")
            return []

    def generate_advanced_charts(self):
        """Generate advanced charts for advanced dashboard."""
        try:
            df = self.analyzer.get_data_as_dataframe(hours_back=24)
            if df.empty:
                return []
            
            charts = []
            
            # Chart 1: Multi-crypto price comparison
            symbols = df['symbol'].unique()[:5]
            fig1 = go.Figure()
            
            for symbol in symbols:
                symbol_df = df[df['symbol'] == symbol].sort_values('timestamp')
                fig1.add_trace(go.Scatter(
                    x=symbol_df['timestamp'],
                    y=symbol_df['price_usd'],
                    mode='lines',
                    name=symbol,
                    line=dict(width=2)
                ))
            
            fig1.update_layout(
                title='Multi-Crypto Price Comparison',
                template='plotly_dark',
                hovermode='x unified',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white')
            )
            
            charts.append({
                'title': 'Multi-Crypto Price Comparison',
                'data': fig1.to_dict()['data'],
                'layout': fig1.to_dict()['layout']
            })
            
            # Chart 2: Market Cap Distribution
            latest = df.sort_values('timestamp').groupby('symbol').last()
            fig2 = go.Figure(data=[go.Pie(
                labels=latest.index,
                values=latest['market_cap'],
                hole=0.3
            )])
            
            fig2.update_layout(
                title='Market Cap Distribution',
                template='plotly_dark',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white')
            )
            
            charts.append({
                'title': 'Market Cap Distribution',
                'data': fig2.to_dict()['data'],
                'layout': fig2.to_dict()['layout']
            })
            
            return charts
        except Exception as e:
            print(f"Error generating advanced charts: {e}")
            return []
