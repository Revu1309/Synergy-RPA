"""Visualization charts for Social Media Trends."""

import json

class SocialTrendsVisualizer:
    """Create visualization charts for social media trends."""
    
    @staticmethod
    def create_trends_bar_chart(trends, limit=20):
        """Create bar chart of top trends by engagement."""
        if not trends:
            return None
        
        sorted_trends = sorted(trends, key=lambda x: x.get('engagement_score', 0), reverse=True)[:limit]
        
        names = [t.get('trend_name', 'Unknown')[:40] for t in sorted_trends]
        engagement = [t.get('engagement_score', 0) for t in sorted_trends]
        
        return {
            'type': 'bar',
            'title': 'Top Trending Topics by Engagement Score',
            'data': [{
                'x': names,
                'y': engagement,
                'type': 'bar',
                'marker': {'color': '#3498db'},
                'hovertemplate': '<b>%{x}</b><br>Engagement: %{y:.2f}<extra></extra>'
            }],
            'layout': {
                'title': 'Top Trending Topics by Engagement Score',
                'xaxis': {'title': 'Trend Name'},
                'yaxis': {'title': 'Engagement Score'},
                'hovermode': 'closest',
                'plot_bgcolor': '#f8f9fa',
                'paper_bgcolor': '#ffffff',
                'margin': {'l': 50, 'r': 50, 't': 50, 'b': 100}
            }
        }
    
    @staticmethod
    def create_platform_comparison_chart(platform_summary):
        """Create bar chart comparing platforms."""
        if not platform_summary:
            return None
        
        platforms = list(platform_summary.keys())
        emerging = [platform_summary[p].get('emerging_count', 0) for p in platforms]
        declining = [platform_summary[p].get('declining_count', 0) for p in platforms]
        avg_engagement = [platform_summary[p].get('avg_engagement', 0) for p in platforms]
        
        return {
            'type': 'platform_comparison',
            'title': 'Platform Comparison',
            'data': [
                {
                    'x': platforms,
                    'y': emerging,
                    'name': 'Emerging Trends',
                    'type': 'bar',
                    'marker': {'color': '#2ecc71'}
                },
                {
                    'x': platforms,
                    'y': declining,
                    'name': 'Declining Trends',
                    'type': 'bar',
                    'marker': {'color': '#e74c3c'}
                }
            ],
            'layout': {
                'title': 'Emerging vs Declining Trends by Platform',
                'xaxis': {'title': 'Platform'},
                'yaxis': {'title': 'Number of Trends'},
                'barmode': 'group',
                'hovermode': 'closest',
                'plot_bgcolor': '#f8f9fa',
                'paper_bgcolor': '#ffffff',
                'margin': {'l': 50, 'r': 50, 't': 50, 'b': 50}
            }
        }
    
    @staticmethod
    def create_sentiment_pie_chart(sentiment_distribution):
        """Create pie chart of sentiment distribution."""
        if not sentiment_distribution:
            return None
        
        labels = list(sentiment_distribution.keys())
        values = list(sentiment_distribution.values())
        
        colors = {
            'positive': '#2ecc71',
            'negative': '#e74c3c',
            'neutral': '#95a5a6',
            'mixed': '#f39c12'
        }
        
        marker_colors = [colors.get(label, '#3498db') for label in labels]
        
        return {
            'type': 'pie',
            'title': 'Sentiment Distribution',
            'data': [{
                'labels': labels,
                'values': values,
                'type': 'pie',
                'marker': {'colors': marker_colors},
                'hovertemplate': '<b>%{label}</b><br>Count: %{value}<extra></extra>'
            }],
            'layout': {
                'title': 'Sentiment Distribution Across Trends',
                'height': 500,
                'paper_bgcolor': '#ffffff',
                'plot_bgcolor': '#f8f9fa'
            }
        }
    
    @staticmethod
    def create_growth_scatter_plot(trends):
        """Create scatter plot of trend rank vs engagement."""
        if not trends:
            return None
        
        ranks = [t.get('rank', 0) for t in trends]
        engagement = [t.get('engagement_score', 0) for t in trends]
        names = [t.get('trend_name', 'Unknown') for t in trends]
        platforms = [t.get('source_platform', 'Unknown') for t in trends]
        
        # Color by platform
        platform_colors = {
            'Reddit': '#ff4500',
            'Hacker News': '#ff6600',
            'GitHub': '#24292e',
            'YouTube': '#ff0000',
            'Stack Overflow': '#f48024',
            'Twitter Trends': '#1da1f2'
        }
        
        colors = [platform_colors.get(p, '#3498db') for p in platforms]
        
        return {
            'type': 'scatter',
            'title': 'Trend Rank vs Engagement',
            'data': [{
                'x': ranks,
                'y': engagement,
                'mode': 'markers',
                'marker': {
                    'size': 10,
                    'color': colors,
                    'opacity': 0.7,
                    'line': {'width': 2, 'color': 'white'}
                },
                'text': [f"{name}<br>{platform}" for name, platform in zip(names, platforms)],
                'hovertemplate': '<b>%{text}</b><br>Rank: %{x}<br>Engagement: %{y:.2f}<extra></extra>',
                'name': 'Trends'
            }],
            'layout': {
                'title': 'Trend Rank vs Engagement Score',
                'xaxis': {'title': 'Rank Position (lower is better)'},
                'yaxis': {'title': 'Engagement Score'},
                'hovermode': 'closest',
                'plot_bgcolor': '#f8f9fa',
                'paper_bgcolor': '#ffffff',
                'margin': {'l': 50, 'r': 50, 't': 50, 'b': 50}
            }
        }
    
    @staticmethod
    def create_emerging_trends_table(trends, limit=15):
        """Create table visualization of emerging trends."""
        if not trends:
            return None
        
        sorted_trends = sorted(trends, key=lambda x: x.get('engagement_score', 0), reverse=True)[:limit]
        
        return {
            'type': 'table',
            'title': 'Top Emerging Trends',
            'trends': sorted_trends
        }
    
    @staticmethod
    def create_platform_trends_pie(platform_summary):
        """Create pie chart of trend distribution by platform."""
        if not platform_summary:
            return None
        
        platforms = list(platform_summary.keys())
        total_trends = [platform_summary[p].get('total_trends', 0) for p in platforms]
        
        colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c']
        
        return {
            'type': 'pie',
            'title': 'Trend Distribution by Platform',
            'data': [{
                'labels': platforms,
                'values': total_trends,
                'type': 'pie',
                'marker': {'colors': colors[:len(platforms)]},
                'hovertemplate': '<b>%{label}</b><br>Trends: %{value}<extra></extra>'
            }],
            'layout': {
                'title': 'Trend Distribution Across Platforms',
                'height': 500,
                'paper_bgcolor': '#ffffff',
                'plot_bgcolor': '#f8f9fa'
            }
        }
    
    @staticmethod
    def create_growth_rate_chart(trends):
        """Create bar chart of growth rates."""
        if not trends:
            return None
        
        sorted_trends = sorted(trends, key=lambda x: x.get('growth_rate', 0), reverse=True)[:15]
        
        names = [t.get('trend_name', 'Unknown')[:35] for t in sorted_trends]
        growth_rates = [t.get('growth_rate', 0) for t in sorted_trends]
        colors = ['#2ecc71' if gr > 0 else '#e74c3c' for gr in growth_rates]
        
        return {
            'type': 'bar',
            'title': 'Trend Growth Rates',
            'data': [{
                'x': names,
                'y': growth_rates,
                'type': 'bar',
                'marker': {'color': colors},
                'hovertemplate': '<b>%{x}</b><br>Growth: %{y:.1f}%<extra></extra>'
            }],
            'layout': {
                'title': 'Top Trends by Growth Rate (%)',
                'xaxis': {'title': 'Trend Name'},
                'yaxis': {'title': 'Growth Rate (%)'},
                'hovermode': 'closest',
                'plot_bgcolor': '#f8f9fa',
                'paper_bgcolor': '#ffffff',
                'margin': {'l': 50, 'r': 50, 't': 50, 'b': 100}
            }
        }
