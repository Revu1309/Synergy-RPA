-- Consolidated SQL schema for RPA project
-- Run with: mysql -u <user> -p rpa_db < database/full_schema.sql
-- All tables are created with IF NOT EXISTS for idempotency

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- User preferences (landing page, roles)
CREATE TABLE IF NOT EXISTS user_preferences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    landing_page VARCHAR(100) NOT NULL DEFAULT '/menu-v2',
    user_role VARCHAR(50) DEFAULT 'admin',
    theme VARCHAR(50) DEFAULT 'default',
    language VARCHAR(20) DEFAULT 'en',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_role (user_role)
);

-- Crypto assets timeseries (prices)
CREATE TABLE IF NOT EXISTS crypto_assets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    name VARCHAR(100) NOT NULL,
    price_usd DECIMAL(20,8),
    market_cap BIGINT,
    volume_24h BIGINT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_symbol_time (symbol, timestamp)
);

-- Alerts for cryptocurrencies
CREATE TABLE IF NOT EXISTS crypto_alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    `condition` ENUM('gt','lt','eq') NOT NULL,
    threshold DECIMAL(30,8) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    notify_method VARCHAR(50) DEFAULT 'console',
    description TEXT,
    alert_mode VARCHAR(20) DEFAULT 'standard',
    custom_metric VARCHAR(50) NULL,
    custom_config TEXT NULL,
    cooldown_minutes INT DEFAULT 15,
    is_triggered BOOLEAN DEFAULT FALSE,
    last_trigger_message TEXT NULL,
    last_evaluated TIMESTAMP NULL,
    last_triggered TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_symbol (symbol),
    INDEX idx_active (is_active),
    INDEX idx_alert_mode (alert_mode)
);

CREATE TABLE IF NOT EXISTS alert_notification_channels (
    id INT AUTO_INCREMENT PRIMARY KEY,
    channel_key VARCHAR(50) NOT NULL UNIQUE,
    module_key VARCHAR(20) NOT NULL DEFAULT 'all',
    channel_type VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    config_json TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_module_key (module_key),
    INDEX idx_channel_type (channel_type),
    INDEX idx_channel_active (is_active)
);

CREATE TABLE IF NOT EXISTS crypto_alert_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    alert_id INT NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    event_type VARCHAR(30) NOT NULL,
    message TEXT,
    observed_price DECIMAL(30,8) NULL,
    metric_value DECIMAL(30,8) NULL,
    payload_json TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_alert_id (alert_id),
    INDEX idx_symbol (symbol),
    INDEX idx_event_type (event_type),
    INDEX idx_created_at (created_at)
);

-- Preferred assets list
CREATE TABLE IF NOT EXISTS preferred_assets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Weather observations
CREATE TABLE IF NOT EXISTS weather_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    location_name VARCHAR(100) NOT NULL,
    country VARCHAR(100),
    latitude DECIMAL(10,6),
    longitude DECIMAL(10,6),
    temperature DECIMAL(5,2),
    feels_like DECIMAL(5,2),
    humidity INT,
    pressure INT,
    wind_speed DECIMAL(6,2),
    wind_direction INT,
    cloudiness INT,
    weather_main VARCHAR(50),
    weather_description VARCHAR(200),
    visibility INT,
    rainfall DECIMAL(6,2),
    snow DECIMAL(6,2),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_location (location_name),
    INDEX idx_timestamp (timestamp)
);

-- Configured weather locations
CREATE TABLE IF NOT EXISTS weather_locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    location_name VARCHAR(100) NOT NULL UNIQUE,
    country VARCHAR(100),
    latitude DECIMAL(10,6) NOT NULL,
    longitude DECIMAL(10,6) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    notes TEXT,
    INDEX idx_active (is_active),
    INDEX idx_location_name (location_name)
);

-- Weather alerts
CREATE TABLE IF NOT EXISTS weather_alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    location_name VARCHAR(100) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    `condition` ENUM('gt','lt','eq') NOT NULL,
    threshold DECIMAL(10,2) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    notify_method VARCHAR(50) DEFAULT 'console',
    description TEXT,
    alert_mode VARCHAR(20) DEFAULT 'standard',
    custom_config TEXT NULL,
    cooldown_minutes INT DEFAULT 15,
    is_triggered BOOLEAN DEFAULT FALSE,
    last_trigger_message TEXT NULL,
    last_evaluated TIMESTAMP NULL,
    last_triggered TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_location (location_name),
    INDEX idx_active (is_active),
    INDEX idx_metric (metric_type)
);

CREATE TABLE IF NOT EXISTS weather_alert_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    alert_id INT NOT NULL,
    location_name VARCHAR(100) NOT NULL,
    event_type VARCHAR(30) NOT NULL,
    message TEXT,
    metric_type VARCHAR(50),
    metric_value DECIMAL(20,6) NULL,
    payload_json TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_alert_id (alert_id),
    INDEX idx_location (location_name),
    INDEX idx_event_type (event_type),
    INDEX idx_created_at (created_at)
);

CREATE TABLE IF NOT EXISTS social_trend_alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    trend_name VARCHAR(255) NOT NULL,
    source_platform VARCHAR(50) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    `condition` ENUM('gt','lt','eq') NOT NULL,
    threshold INT NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    notify_method VARCHAR(50) DEFAULT 'console',
    description TEXT,
    alert_mode VARCHAR(20) DEFAULT 'standard',
    custom_config TEXT NULL,
    cooldown_minutes INT DEFAULT 15,
    is_triggered BOOLEAN DEFAULT FALSE,
    last_trigger_message TEXT NULL,
    last_evaluated TIMESTAMP NULL,
    last_triggered TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_trend (trend_name),
    INDEX idx_platform (source_platform),
    INDEX idx_active (is_active),
    INDEX idx_metric (metric_type)
);

CREATE TABLE IF NOT EXISTS social_trend_alert_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    alert_id INT NOT NULL,
    trend_name VARCHAR(255) NOT NULL,
    source_platform VARCHAR(50) NOT NULL,
    event_type VARCHAR(30) NOT NULL,
    message TEXT,
    metric_type VARCHAR(50),
    metric_value DECIMAL(20,6) NULL,
    payload_json TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_alert_id (alert_id),
    INDEX idx_trend (trend_name),
    INDEX idx_platform (source_platform),
    INDEX idx_event_type (event_type),
    INDEX idx_created_at (created_at)
);

-- Predefined cities (for weather module)
CREATE TABLE IF NOT EXISTS predefined_cities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city_name VARCHAR(100) NOT NULL UNIQUE,
    country VARCHAR(100) NOT NULL,
    latitude DECIMAL(10,6) NOT NULL,
    longitude DECIMAL(10,6) NOT NULL,
    region VARCHAR(100),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_active (is_active),
    INDEX idx_country (country)
);

-- Social media / trends tables
CREATE TABLE IF NOT EXISTS social_trends (
    id INT AUTO_INCREMENT PRIMARY KEY,
    trend_name VARCHAR(255) NOT NULL,
    trend_type ENUM('keyword', 'hashtag', 'topic') NOT NULL DEFAULT 'keyword',
    source_platform VARCHAR(50) NOT NULL,
    rank_position INT,
    volume INT,
    engagement_count BIGINT,
    trend_url VARCHAR(1000),
    interaction_rate DECIMAL(6,3),
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

CREATE TABLE IF NOT EXISTS trend_analysis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    trend_name VARCHAR(255) NOT NULL,
    source_platform VARCHAR(50) NOT NULL,
    analysis_type VARCHAR(100),
    growth_rate DECIMAL(8,2),
    peak_time DATETIME,
    decline_rate DECIMAL(8,2),
    avg_sentiment DECIMAL(3,2),
    total_mentions BIGINT,
    unique_users BIGINT,
    engagement_score DECIMAL(8,2),
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

CREATE TABLE IF NOT EXISTS social_media_sources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    platform_name VARCHAR(50) NOT NULL UNIQUE,
    platform_display_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    api_endpoint VARCHAR(500),
    scraper_enabled BOOLEAN DEFAULT TRUE,
    update_frequency_minutes INT DEFAULT 60,
    last_sync TIMESTAMP,
    data_collection_method ENUM('api','scraper','rss','hybrid') DEFAULT 'scraper',
    country_code VARCHAR(10),
    language_code VARCHAR(10),
    max_trends INT DEFAULT 50,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_active (is_active),
    INDEX idx_platform (platform_name)
);

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

-- Signal fusion index snapshots
CREATE TABLE IF NOT EXISTS signal_fusion_index (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    crypto_score DECIMAL(6,2) NOT NULL,
    social_score DECIMAL(6,2) NOT NULL,
    weather_score DECIMAL(6,2) NOT NULL,
    fusion_score DECIMAL(6,2) NOT NULL,
    confidence_level VARCHAR(20) NOT NULL,
    INDEX idx_timestamp (timestamp)
);

SET FOREIGN_KEY_CHECKS = 1;
