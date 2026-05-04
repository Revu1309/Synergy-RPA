
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
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='rgba(255,255,255,0.7)'),
                    xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
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
