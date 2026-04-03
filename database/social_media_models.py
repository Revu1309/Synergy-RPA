"""Database models and functions for Social Media Trends."""

from .connection import create_connection
from datetime import datetime, timedelta

# ==================== SOCIAL MEDIA TRENDS MODELS ====================

def create_social_trends_tables():
    """Create all social media trends tables if they don't exist."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        
        try:
            # Social Trends Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS social_trends (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    trend_name VARCHAR(255) NOT NULL,
                    trend_type ENUM('keyword', 'hashtag', 'topic') NOT NULL DEFAULT 'keyword',
                    source_platform VARCHAR(50) NOT NULL,
                    rank_position INT,
                    volume INT,
                    engagement_count BIGINT,
                    trend_url VARCHAR(1000),
                    interaction_rate DECIMAL(6, 3),
                    momentum VARCHAR(20),
                    sentiment ENUM('positive', 'negative', 'neutral', 'mixed') DEFAULT 'neutral',
                    related_keywords TEXT,
                    description TEXT,
                    data_collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_platform (source_platform),
                    INDEX idx_timestamp (data_collected_at),
                    INDEX idx_trend_name (trend_name),
                    INDEX idx_rank (rank_position)
                )
            """)
            
            # Trend Details Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trend_details (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    trend_id INT NOT NULL,
                    metric_name VARCHAR(100),
                    metric_value VARCHAR(500),
                    category VARCHAR(100),
                    location VARCHAR(100),
                    language VARCHAR(10),
                    platform_specific_id VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (trend_id) REFERENCES social_trends(id) ON DELETE CASCADE,
                    INDEX idx_trend_id (trend_id),
                    INDEX idx_metric (metric_name)
                )
            """)
            
            # Historical Trends Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trend_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    trend_name VARCHAR(255) NOT NULL,
                    source_platform VARCHAR(50) NOT NULL,
                    rank_at_time INT,
                    volume_at_time INT,
                    engagement_at_time BIGINT,
                    sentiment_at_time ENUM('positive', 'negative', 'neutral', 'mixed'),
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_trend_name (trend_name),
                    INDEX idx_platform (source_platform),
                    INDEX idx_timestamp (recorded_at)
                )
            """)

            # Safe schema migrations for existing deployments.
            try:
                cursor.execute("ALTER TABLE social_trends ADD COLUMN trend_url VARCHAR(1000) NULL")
            except Exception:
                pass
            
            # Trend Analysis Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trend_analysis (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    trend_name VARCHAR(255) NOT NULL,
                    source_platform VARCHAR(50) NOT NULL,
                    analysis_type VARCHAR(100),
                    growth_rate DECIMAL(8, 2),
                    peak_time DATETIME,
                    decline_rate DECIMAL(8, 2),
                    avg_sentiment DECIMAL(3, 2),
                    total_mentions BIGINT,
                    unique_users BIGINT,
                    engagement_score DECIMAL(8, 2),
                    prediction_status VARCHAR(50),
                    is_emerging BOOLEAN DEFAULT FALSE,
                    is_declining BOOLEAN DEFAULT FALSE,
                    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_trend_name (trend_name),
                    INDEX idx_platform (source_platform),
                    INDEX idx_emerging (is_emerging),
                    INDEX idx_timestamp (analyzed_at)
                )
            """)
            
            # Social Media Sources Configuration
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS social_media_sources (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    platform_name VARCHAR(50) NOT NULL UNIQUE,
                    platform_display_name VARCHAR(100),
                    is_active BOOLEAN DEFAULT TRUE,
                    api_endpoint VARCHAR(500),
                    scraper_enabled BOOLEAN DEFAULT TRUE,
                    update_frequency_minutes INT DEFAULT 60,
                    last_sync TIMESTAMP,
                    data_collection_method ENUM('api', 'scraper', 'rss', 'hybrid') DEFAULT 'scraper',
                    country_code VARCHAR(10),
                    language_code VARCHAR(10),
                    max_trends INT DEFAULT 50,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_active (is_active),
                    INDEX idx_platform (platform_name)
                )
            """)
            
            # Trending Keywords Cache
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trending_keywords (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    keyword VARCHAR(255) NOT NULL,
                    platform VARCHAR(50),
                    frequency INT,
                    last_seen TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_keyword_platform (keyword, platform),
                    INDEX idx_keyword (keyword),
                    INDEX idx_platform (platform),
                    INDEX idx_active (is_active)
                )
            """)
            
            connection.commit()
            print("✓ Social media trends tables created successfully")
            
        except Exception as e:
            print(f"Error creating social media tables: {e}")
        finally:
            cursor.close()
            connection.close()

# ==================== INSERT FUNCTIONS ====================

def insert_social_trend(
    trend_name,
    trend_type,
    source_platform,
    rank_position=None,
    volume=None,
    engagement_count=None,
    engagement=None,
    sentiment='neutral',
    related_keywords=None,
    description=None,
    trend_url=None,
):
    """Insert a new social trend into the database."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            # Support both `engagement_count` and legacy `engagement` keyword
            _engagement = engagement_count if engagement_count is not None else engagement
            cursor.execute("""
                INSERT INTO social_trends 
                (trend_name, trend_type, source_platform, rank_position, volume, 
                 engagement_count, sentiment, related_keywords, description, trend_url, data_collected_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (trend_name, trend_type, source_platform, rank_position, volume,
                  _engagement, sentiment, related_keywords, description, trend_url, datetime.now()))
            
            connection.commit()
            return True
        except Exception as e:
            print(f"Error inserting social trend: {e}")
            return False
        finally:
            cursor.close()
            connection.close()
    return False

def insert_trend_history(trend_name, source_platform, rank_at_time=None, volume_at_time=None,
                        engagement_at_time=None, sentiment_at_time=None):
    """Insert trend history record."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO trend_history 
                (trend_name, source_platform, rank_at_time, volume_at_time, 
                 engagement_at_time, sentiment_at_time, recorded_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (trend_name, source_platform, rank_at_time, volume_at_time,
                  engagement_at_time, sentiment_at_time, datetime.now()))
            
            connection.commit()
            cursor.close()
            connection.close()
            return True
        except Exception as e:
            print(f"Error inserting trend history: {e}")
            return False
    return False

def insert_trend_analysis(trend_name, source_platform, growth_rate=None, peak_time=None,
                         decline_rate=None, avg_sentiment=None, total_mentions=None,
                         unique_users=None, engagement_score=None, is_emerging=False,
                         is_declining=False, prediction_status=None):
    """Insert trend analysis record."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO trend_analysis 
                (trend_name, source_platform, growth_rate, peak_time, decline_rate,
                 avg_sentiment, total_mentions, unique_users, engagement_score,
                 is_emerging, is_declining, prediction_status, analyzed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (trend_name, source_platform, growth_rate, peak_time, decline_rate,
                  avg_sentiment, total_mentions, unique_users, engagement_score,
                  is_emerging, is_declining, prediction_status, datetime.now()))
            
            connection.commit()
            cursor.close()
            connection.close()
            return True
        except Exception as e:
            print(f"Error inserting trend analysis: {e}")
            return False
    return False

# ==================== GET FUNCTIONS ====================

def get_trends_by_platform(platform, limit=50):
    """Get trending topics by platform."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT id, trend_name, trend_type, rank_position, volume, 
                       engagement_count, sentiment, description, trend_url, data_collected_at
                FROM social_trends
                WHERE source_platform = %s
                ORDER BY rank_position ASC, volume DESC
                LIMIT %s
            """, (platform, limit))
            
            results = cursor.fetchall()
            cursor.close()
            connection.close()
            return results
        except Exception as e:
            print(f"Error getting trends: {e}")
            return []
    return []

def get_all_trends(limit=500):
    """Get latest trending topics from all platforms with balanced ordering."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            # Prefer latest snapshot table to avoid historical duplicates dominating
            # the dashboard and to preserve cross-platform visibility.
            try:
                cursor.execute("""
                    SELECT source_platform, trend_name, 'topic' AS trend_type, rank_position, volume,
                           engagement_count, sentiment, NULL AS description, trend_url, data_collected_at
                    FROM social_latest
                    ORDER BY COALESCE(NULLIF(engagement_count, 0), NULLIF(volume, 0), 0) DESC,
                             rank_position ASC,
                             source_platform ASC
                    LIMIT %s
                """, (limit,))
            except Exception:
                # Fallback for older databases without social_latest.
                cursor.execute("""
                    SELECT source_platform, trend_name, trend_type, rank_position, volume,
                           engagement_count, sentiment, description, trend_url, data_collected_at
                    FROM social_trends
                    ORDER BY COALESCE(NULLIF(engagement_count, 0), NULLIF(volume, 0), 0) DESC,
                             rank_position ASC,
                             source_platform ASC
                    LIMIT %s
                """, (limit,))
            
            results = cursor.fetchall()
            cursor.close()
            connection.close()
            return results
        except Exception as e:
            print(f"Error getting all trends: {e}")
            return []
    return []

def get_all_active_platforms():
    """Get all active social media platforms."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT id, platform_name, platform_display_name, update_frequency_minutes
                FROM social_media_sources
                WHERE is_active = TRUE
                ORDER BY platform_name
            """)
            
            results = cursor.fetchall()
            cursor.close()
            connection.close()
            return results
        except Exception as e:
            print(f"Error getting platforms: {e}")
            return []
    return []

def get_emerging_trends(hours=24, limit=20):
    """Get emerging trends from last N hours."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT trend_name, source_platform, growth_rate, engagement_score, 
                       avg_sentiment, analyzed_at
                FROM trend_analysis
                WHERE is_emerging = TRUE
                AND analyzed_at >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                ORDER BY growth_rate DESC, engagement_score DESC
                LIMIT %s
            """, (hours, limit))
            
            results = cursor.fetchall()
            cursor.close()
            connection.close()
            return results
        except Exception as e:
            print(f"Error getting emerging trends: {e}")
            return []
    return []

def get_trending_keywords(platform=None, limit=30):
    """Get trending keywords, optionally filtered by platform."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            if platform:
                cursor.execute("""
                    SELECT keyword, platform, frequency, last_seen
                    FROM trending_keywords
                    WHERE platform = %s AND is_active = TRUE
                    ORDER BY frequency DESC
                    LIMIT %s
                """, (platform, limit))
            else:
                cursor.execute("""
                    SELECT keyword, platform, frequency, last_seen
                    FROM trending_keywords
                    WHERE is_active = TRUE
                    ORDER BY frequency DESC, last_seen DESC
                    LIMIT %s
                """, (limit,))
            
            results = cursor.fetchall()
            cursor.close()
            connection.close()
            return results
        except Exception as e:
            print(f"Error getting trending keywords: {e}")
            return []
    return []

def get_trend_history(trend_name, platform, days=30):
    """Get historical data for a specific trend."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT trend_name, source_platform, rank_at_time, volume_at_time,
                       engagement_at_time, sentiment_at_time, recorded_at
                FROM trend_history
                WHERE trend_name = %s AND source_platform = %s
                AND recorded_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                ORDER BY recorded_at ASC
            """, (trend_name, platform, days))
            
            results = cursor.fetchall()
            cursor.close()
            connection.close()
            return results
        except Exception as e:
            print(f"Error getting trend history: {e}")
            return []
    return []

def clear_old_trends(days=30):
    """Clear trends older than N days."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                DELETE FROM social_trends
                WHERE data_collected_at < DATE_SUB(NOW(), INTERVAL %s DAY)
            """, (days,))
            
            deleted = cursor.rowcount
            connection.commit()
            cursor.close()
            connection.close()
            return deleted
        except Exception as e:
            print(f"Error clearing old trends: {e}")
            return 0
    return 0
