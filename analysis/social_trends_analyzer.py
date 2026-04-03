"""Social Media Trends Analyzer - Generate insights from trend data."""

from database.connection import create_connection
from datetime import datetime, timedelta
import statistics

class TrendsAnalyzer:
    """Analyze social media trends and generate insights."""
    
    def __init__(self):
        pass
    
    def analyze_trends(self, trends):
        """Analyze a list of trends and generate insights."""
        if not trends:
            return []
        
        analysis_results = []
        
        # Group trends by platform
        platforms = {}
        for trend in trends:
            platform = trend.get('source_platform', 'Unknown')
            if platform not in platforms:
                platforms[platform] = []
            platforms[platform].append(trend)
        
        # Analyze each platform
        for platform, platform_trends in platforms.items():
            platform_analysis = self._analyze_platform_trends(platform, platform_trends)
            analysis_results.extend(platform_analysis)
        
        return analysis_results
    
    def _analyze_platform_trends(self, platform, trends):
        """Analyze trends for a specific platform."""
        analysis = []
        
        if not trends:
            return analysis
        
        # Calculate statistics
        volumes = [t.get('volume', 0) for t in trends if t.get('volume')]
        engagements = [t.get('engagement_count', 0) for t in trends if t.get('engagement_count')]
        
        avg_volume = statistics.mean(volumes) if volumes else 0
        avg_engagement = statistics.mean(engagements) if engagements else 0
        
        # Identify emerging trends (high engagement relative to rank)
        for idx, trend in enumerate(trends[:20]):
            volume = trend.get('volume', 0)
            engagement = trend.get('engagement_count', 0)
            rank = trend.get('rank_position', idx + 1)
            
            # Calculate engagement score
            engagement_score = (engagement / (rank + 1)) * 100 if rank > 0 else engagement
            
            # Determine if emerging
            is_emerging = engagement_score > (avg_engagement * 1.5) and rank <= 10
            
            # Estimate growth rate
            growth_rate = ((engagement - volume) / (volume + 1)) * 100 if volume else 0
            
            analysis_item = {
                'trend_name': trend.get('trend_name'),
                'source_platform': platform,
                'engagement_score': round(engagement_score, 2),
                'growth_rate': round(growth_rate, 2),
                'is_emerging': is_emerging,
                'is_declining': growth_rate < -20,
                'sentiment': trend.get('sentiment', 'neutral'),
                'rank': rank,
                'volume': volume,
                'engagement': engagement
            }
            analysis.append(analysis_item)
        
        return analysis
    
    def calculate_trend_momentum(self, current_rank, previous_rank):
        """Calculate momentum: trending up/down/stable."""
        if previous_rank is None:
            return "new"
        
        diff = previous_rank - current_rank
        if diff > 5:
            return "rising"
        elif diff < -5:
            return "falling"
        else:
            return "stable"
    
    def identify_related_keywords(self, trend_name):
        """Identify keywords related to a trend."""
        # Simple keyword extraction (can be enhanced with NLP)
        keywords = trend_name.lower().split()
        return [k for k in keywords if len(k) > 3]
    
    def calculate_sentiment_score(self, trend_name):
        """Calculate sentiment for a trend (simplified)."""
        positive_words = ['grow', 'rise', 'gain', 'up', 'success', 'increase', 'trending', 'popular']
        negative_words = ['fall', 'drop', 'crash', 'down', 'decline', 'dead', 'fail', 'loss']
        
        trend_lower = trend_name.lower()
        pos_count = sum(1 for word in positive_words if word in trend_lower)
        neg_count = sum(1 for word in negative_words if word in trend_lower)
        
        if pos_count > neg_count:
            return 'positive'
        elif neg_count > pos_count:
            return 'negative'
        else:
            return 'neutral'
    
    def get_trend_category(self, trend_name):
        """Categorize a trend based on keywords."""
        trend_lower = trend_name.lower()
        
        categories = {
            'Technology': ['ai', 'tech', 'software', 'app', 'digital', 'code', 'programming', 'python', 'javascript'],
            'Business': ['startup', 'business', 'market', 'money', 'finance', 'growth', 'investment'],
            'Entertainment': ['movie', 'music', 'game', 'celebrity', 'film', 'actor', 'show'],
            'Science': ['science', 'research', 'study', 'discovery', 'medical', 'health'],
            'Sports': ['sport', 'game', 'player', 'team', 'match', 'football', 'basketball'],
            'Politics': ['politics', 'election', 'government', 'vote', 'leader', 'congress'],
            'Social': ['social', 'community', 'people', 'culture', 'trending', 'viral']
        }
        
        for category, keywords in categories.items():
            if any(keyword in trend_lower for keyword in keywords):
                return category
        
        return 'General'

class TrendInsights:
    """Generate insights from trend data."""
    
    @staticmethod
    def get_top_emerging_trends(analysis, limit=10):
        """Get top emerging trends."""
        emerging = [t for t in analysis if t.get('is_emerging', False)]
        return sorted(emerging, key=lambda x: x.get('engagement_score', 0), reverse=True)[:limit]
    
    @staticmethod
    def get_declining_trends(analysis, limit=10):
        """Get declining trends."""
        declining = [t for t in analysis if t.get('is_declining', False)]
        return sorted(declining, key=lambda x: x.get('growth_rate', 0))[:limit]
    
    @staticmethod
    def get_trends_by_platform(analysis, platform):
        """Get trends for a specific platform."""
        return [t for t in analysis if t.get('source_platform') == platform]
    
    @staticmethod
    def get_high_engagement_trends(analysis, limit=10):
        """Get trends with highest engagement."""
        return sorted(analysis, key=lambda x: x.get('engagement_score', 0), reverse=True)[:limit]
    
    @staticmethod
    def get_sentiment_distribution(analysis):
        """Get sentiment distribution across trends."""
        sentiments = {}
        for item in analysis:
            sentiment = item.get('sentiment', 'neutral')
            sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
        return sentiments
    
    @staticmethod
    def get_platform_summary(analysis):
        """Get summary statistics by platform."""
        platforms = {}
        
        for item in analysis:
            platform = item.get('source_platform')
            if platform not in platforms:
                platforms[platform] = {
                    'total_trends': 0,
                    'avg_engagement': 0,
                    'emerging_count': 0,
                    'declining_count': 0
                }
            
            platforms[platform]['total_trends'] += 1
            platforms[platform]['avg_engagement'] += item.get('engagement_score', 0)
            
            if item.get('is_emerging'):
                platforms[platform]['emerging_count'] += 1
            if item.get('is_declining'):
                platforms[platform]['declining_count'] += 1
        
        # Calculate averages
        for platform in platforms:
            total = platforms[platform]['total_trends']
            if total > 0:
                platforms[platform]['avg_engagement'] = round(
                    platforms[platform]['avg_engagement'] / total, 2
                )
        
        return platforms
