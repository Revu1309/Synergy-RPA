-- Social Media Trends Database Schema
-- Stores trending keywords, hashtags, and metadata from multiple platforms

-- 1. Trending Topics Table
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
);

-- 2. Trend Details Table (stores additional metadata)
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
);

-- 3. Historical Trends Table (track trends over time)
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
);

-- 4. Trend Analysis Table (insights and patterns)
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
);

-- 5. Social Media Sources Configuration
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
);

-- 6. Trend Categories Table
CREATE TABLE IF NOT EXISTS trend_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    category_description TEXT,
    color_code VARCHAR(7),
    icon VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (category_name)
);

-- 7. Trending Keywords (cache for quick access)
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
);
