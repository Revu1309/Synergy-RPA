# SYNERGY RPA - Vercel Postgres Deployment (Build 1778082000)
"""Main Flask application with authentication and menu system."""

from flask import Flask, render_template, request, jsonify, redirect, session, url_for
from flask_cors import CORS
from functools import wraps
import sys
import os
import json
import html as html_escape
import re
from datetime import timedelta, datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.auth import AuthManager
from analysis.analyzer import CryptoAnalyzer
from analysis.weather_analyzer import WeatherAnalyzer
from visualization.charts import CryptoVisualizer
from visualization.weather_charts import WeatherVisualizer
from database.preferred_assets import PreferredAssetsManager
from database.weather_locations import WeatherLocationsManager
from database.predefined_cities import PredefinedCitiesManager
from scraper.weather import get_weather_data
from database.models import (
    insert_weather_data,
    upsert_weather_latest,
    clear_crypto_data,
    get_signal_fusion_index,
)
from database.connection import create_connection
from config.config import (
    SCRAPE_INTERVAL_MINUTES,
    SOCIAL_SYNC_INTERVAL_MINUTES,
    WEATHER_SYNC_INTERVAL_MINUTES,
)
from database.access_control import (
    create_access_control_tables,
    seed_default_access_config,
    is_admin_user,
    get_user_menu_modules,
    get_first_allowed_route,
    get_modules_with_pages,
    get_user_allowed_page_keys,
    set_user_allowed_pages,
    list_users,
    create_user,
    update_user,
    reset_user_password,
    user_can_access_path,
    normalize_path,
)
from database.ui_settings import get_user_theme, set_user_theme
from dashboard.menu_config import MENU_ITEMS, merge_menu_with_db_modules
import data_store

# Real-time data infrastructure
from utils.realtime_data import get_realtime_cache
from dashboard.realtime_api import create_realtime_endpoints
from utils.data_service import DataService

app = Flask(__name__, 
            static_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static'),
            template_folder='templates')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'rpa-framework-dev-secret')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
CORS(app)
app.config['ENABLE_MENU_REDIRECT'] = True

# Initialize real-time cache and register endpoints
cache = get_realtime_cache()
create_realtime_endpoints(app, cache, None)

THEME_PRESETS = {
    "dark_glass": {
        "colors": {
            "bg_base": "#0A0A0E",
            "bg_secondary": "#111116",
            "bg_panel": "rgba(17, 17, 22, 0.65)",
            "bg_glass": "rgba(255, 255, 255, 0.03)",
            "bg_glass_hover": "rgba(255, 255, 255, 0.06)",
            "accent_primary": "#5B5BFF",
            "accent_secondary": "#A855F7",
            "accent_tertiary": "#14F1D9",
            "accent_grad": "linear-gradient(135deg, #5B5BFF, #A855F7)",
            "text_primary": "#FFFFFF",
            "text_secondary": "#9CA3AF",
            "text_tertiary": "#6B7280",
            "text_inverse": "#FFFFFF",
            "border_subtle": "rgba(255, 255, 255, 0.06)",
            "border_focus": "rgba(91, 91, 255, 0.4)",
            "glow_primary": "rgba(91, 91, 255, 0.25)",
            "glow_secondary": "rgba(168, 85, 247, 0.25)",
            "ambient_primary": "rgba(91, 91, 255, 0.15)",
            "ambient_secondary": "rgba(168, 85, 247, 0.12)"
        },
        "typography": {
            "font_primary": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
            "font_heading": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
            "font_weight_heading": "700"
        },
        "geometry": {
            "radius_sm": "6px",
            "radius_md": "12px",
            "radius_lg": "24px",
            "radius_xl": "32px",
            "radius_full": "9999px",
            "glass_blur": "blur(24px)",
            "shadow_sm": "0 2px 8px rgba(0,0,0,0.4)",
            "shadow_md": "0 8px 24px rgba(0,0,0,0.5)",
            "shadow_lg": "0 16px 40px rgba(0,0,0,0.6)",
            "shadow_xl": "0 24px 60px rgba(0,0,0,0.7)"
        }
    },
    "midnight_gradient": {
        "colors": {
            "bg_base": "#060411",
            "bg_secondary": "#0A0818",
            "bg_panel": "rgba(10, 8, 24, 0.6)",
            "bg_glass": "rgba(255, 255, 255, 0.04)",
            "bg_glass_hover": "rgba(255, 255, 255, 0.08)",
            "accent_primary": "#FF3366",
            "accent_secondary": "#7C3AED",
            "accent_tertiary": "#06B6D4",
            "accent_grad": "linear-gradient(135deg, #FF3366, #7C3AED)",
            "text_primary": "#FFFFFF",
            "text_secondary": "#A78BFA",
            "text_tertiary": "#6D28D9",
            "text_inverse": "#FFFFFF",
            "border_subtle": "rgba(124, 58, 237, 0.15)",
            "border_focus": "rgba(255, 51, 102, 0.5)",
            "glow_primary": "rgba(255, 51, 102, 0.3)",
            "glow_secondary": "rgba(124, 58, 237, 0.3)",
            "ambient_primary": "rgba(255, 51, 102, 0.15)",
            "ambient_secondary": "rgba(124, 58, 237, 0.15)"
        },
        "typography": {
            "font_primary": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
            "font_heading": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
            "font_weight_heading": "700"
        },
        "geometry": {
            "radius_sm": "8px",
            "radius_md": "16px",
            "radius_lg": "32px",
            "radius_xl": "48px",
            "radius_full": "9999px",
            "glass_blur": "blur(32px)",
            "shadow_sm": "0 4px 12px rgba(0,0,0,0.3)",
            "shadow_md": "0 8px 24px rgba(0,0,0,0.4)",
            "shadow_lg": "0 16px 48px rgba(0,0,0,0.5)",
            "shadow_glow": "0 8px 32px rgba(255, 51, 102, 0.25)"
        }
    }
}
def get_plotly_dark_layout(title, xaxis_title=None, yaxis_title=None, height=350, hovermode='x unified'):
    layout = {
        'title': title,
        'height': height,
        'hovermode': hovermode,
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'font': {'color': 'rgba(255,255,255,0.7)', 'family': 'Inter'},
        'margin': {'l': 50, 'r': 50, 't': 50, 'b': 50},
        'xaxis': {
            'gridcolor': 'rgba(255,255,255,0.05)',
            'zerolinecolor': 'rgba(255,255,255,0.1)',
            'title': xaxis_title if xaxis_title else ''
        },
        'yaxis': {
            'gridcolor': 'rgba(255,255,255,0.05)',
            'zerolinecolor': 'rgba(255,255,255,0.1)',
            'title': yaxis_title if yaxis_title else ''
        }
    }
    return layout


# Lazy initialization - Crypto
analyzer = None
visualizer = None

# Lazy initialization - Weather
weather_analyzer = None
weather_visualizer = None

def get_analyzer():
    global analyzer
    if analyzer is None:
        print("Initializing CryptoAnalyzer...")
        analyzer = CryptoAnalyzer()
        print("CryptoAnalyzer initialized")
    return analyzer

def get_visualizer():
    global visualizer
    if visualizer is None:
        print("Initializing CryptoVisualizer...")
        visualizer = CryptoVisualizer()
        print("CryptoVisualizer initialized")
    return visualizer

def get_weather_analyzer():
    global weather_analyzer
    if weather_analyzer is None:
        print("Initializing WeatherAnalyzer...")
        weather_analyzer = WeatherAnalyzer()
        print("WeatherAnalyzer initialized")
    return weather_analyzer

def get_weather_visualizer():
    global weather_visualizer
    if weather_visualizer is None:
        print("Initializing WeatherVisualizer...")
        weather_visualizer = WeatherVisualizer()
        print("WeatherVisualizer initialized")
    return weather_visualizer

# ==================== WEATHER SYNC SCHEDULER ====================

def sync_weather_job():
    """Background job to sync weather data with proper timestamps and real-time updates."""
    import logging
    start_ts = datetime.utcnow()
    logging.info(f"[WEATHER] Job start: {start_ts.isoformat()}Z")
    
    try:
        # Get active locations from database
        locations = WeatherLocationsManager.get_all_locations(active_only=True)

        if not locations:
            logging.info("[WEATHER] No active locations configured")
            return

        # Fetch weather data for active locations
        weather_data = get_weather_data(locations)

        # Normalize and validate data
        try:
            normalized_weather = DataService.WEATHER.normalize_weather_list(weather_data)
            logging.info(f"[WEATHER] Normalized {len(normalized_weather)} weather records")
        except Exception as normalize_err:
            logging.warning(f"[WEATHER] Data normalization warning: {normalize_err}")
            normalized_weather = weather_data

        # Insert into database
        success_count = 0
        for data in normalized_weather:
            try:
                # Historical insert
                insert_weather_data(
                    location_name=data.get('location_name'),
                    country=data.get('country'),
                    latitude=data.get('latitude'),
                    longitude=data.get('longitude'),
                    temperature=data.get('temperature'),
                    feels_like=data.get('feels_like'),
                    humidity=data.get('humidity'),
                    pressure=data.get('pressure'),
                    wind_speed=data.get('wind_speed'),
                    wind_direction=data.get('wind_direction'),
                    cloudiness=data.get('cloudiness'),
                    weather_main=data.get('weather_main'),
                    weather_description=data.get('weather_description'),
                    visibility=data.get('visibility'),
                    rainfall=data.get('rainfall'),
                    snow=data.get('snow', 0)
                )
                upsert_weather_latest(
                    location_name=data.get('location_name'),
                    country=data.get('country'),
                    latitude=data.get('latitude'),
                    longitude=data.get('longitude'),
                    temperature=data.get('temperature'),
                    feels_like=data.get('feels_like'),
                    humidity=data.get('humidity'),
                    pressure=data.get('pressure'),
                    wind_speed=data.get('wind_speed'),
                    wind_direction=data.get('wind_direction'),
                    cloudiness=data.get('cloudiness'),
                    weather_main=data.get('weather_main'),
                    weather_description=data.get('weather_description'),
                    visibility=data.get('visibility'),
                    rainfall=data.get('rainfall'),
                    snow=data.get('snow', 0)
                )
                success_count += 1
            except Exception as e:
                logging.warning(f"[WEATHER] Failed to insert {data.get('location_name')}: {e}")

        # Update real-time cache with normalized data
        try:
            weather_dict = {w['location_name']: w for w in normalized_weather}
            cache.update_weather(weather_dict)
            logging.info(f"[WEATHER] Cache updated with {len(normalized_weather)} locations")
        except Exception as cache_err:
            logging.warning(f"[WEATHER] Failed to update cache: {cache_err}")

        logging.info(f"[WEATHER] Weather sync completed! Inserted {success_count}/{len(normalized_weather)} records")
        try:
            from database.alert_models import evaluate_weather_alerts
            results = evaluate_weather_alerts(trigger_source="scheduler", dispatch_notifications=True)
            triggered_count = len([r for r in results if r.get("is_match") and not r.get("in_cooldown")])
            logging.info("[ALERTS] Evaluated %d weather alerts, %d newly triggered", len(results), triggered_count)
        except Exception as alert_err:
            logging.error(f"[ALERTS] Error evaluating weather alerts: {alert_err}")

    except Exception as e:
        logging.error(f"[WEATHER] Error in weather sync job: {e}")
    finally:
        end_ts = datetime.utcnow()
        logging.info(f"[WEATHER] Job end: {end_ts.isoformat()}Z")

# Note: scheduler startup is intentionally NOT performed here.
# The `sync_weather_job()` function is defined in this module so an
# external scheduler (started from the main process) can import and
# schedule it. This prevents the Flask app from starting schedulers on import.

# ==================== CRYPTO DATA INITIALIZATION ====================

def init_crypto_assets():
    """Initialize 15 crypto assets and populate test data on startup."""
    try:
        from database.connection import create_connection
        from datetime import datetime, timedelta
        import random
        
        conn = create_connection()
        if not conn:
            print("Failed to initialize crypto assets: Database connection failed")
            return
        
        cursor = conn.cursor()
        
        # Check if assets already exist
        cursor.execute("SELECT COUNT(*) FROM preferred_assets")
        asset_count = cursor.fetchone()[0]
        
        if asset_count >= 15:
            print(" Crypto assets already initialized (15 assets found)")
            cursor.close()
            conn.close()
            return
        
        # Define 15 crypto assets
        assets_to_load = [
            ('BTC', 'Bitcoin'),
            ('ETH', 'Ethereum'),
            ('XRP', 'Ripple'),
            ('ADA', 'Cardano'),
            ('SOL', 'Solana'),
            ('DOGE', 'Dogecoin'),
            ('AVAX', 'Avalanche'),
            ('MATIC', 'Polygon'),
            ('LIT', 'Litecoin'),
            ('XLM', 'Stellar'),
            ('VET', 'VeChain'),
            ('LINK', 'Chainlink'),
            ('NEAR', 'Near Protocol'),
            ('FIL', 'Filecoin'),
            ('GRT', 'The Graph'),
        ]
        
        # Clear and reload assets
        cursor.execute("DELETE FROM preferred_assets")
        print("Initializing crypto assets...")
        
        for symbol, name in assets_to_load:
            cursor.execute(
                "INSERT INTO preferred_assets (symbol, name) VALUES (%s, %s)",
                (symbol, name)
            )
        
        conn.commit()
        print(f" Loaded {len(assets_to_load)} crypto assets")
        
        # Check if crypto_assets has data
        cursor.execute("SELECT COUNT(*) FROM crypto_assets")
        crypto_count = cursor.fetchone()[0]
        
        if crypto_count >= 450:
            print(f" Crypto data already populated ({crypto_count} records)")
            cursor.close()
            conn.close()
            return
        
        # Populate test data for 30 days
        print("Populating crypto test data (450 records)...")
        
        price_ranges = {
            'BTC': (20000, 45000),
            'ETH': (1500, 3500),
            'XRP': (0.40, 1.20),
            'ADA': (0.30, 0.90),
            'SOL': (20, 150),
            'DOGE': (0.05, 0.20),
            'AVAX': (15, 80),
            'MATIC': (0.60, 2.50),
            'LIT': (50, 200),
            'XLM': (0.10, 0.40),
            'VET': (0.015, 0.10),
            'LINK': (6, 35),
            'NEAR': (2, 10),
            'FIL': (4, 25),
            'GRT': (0.10, 0.50),
        }
        
        asset_names = {
            'BTC': 'Bitcoin',
            'ETH': 'Ethereum',
            'XRP': 'Ripple',
            'ADA': 'Cardano',
            'SOL': 'Solana',
            'DOGE': 'Dogecoin',
            'AVAX': 'Avalanche',
            'MATIC': 'Polygon',
            'LIT': 'Litecoin',
            'XLM': 'Stellar',
            'VET': 'VeChain',
            'LINK': 'Chainlink',
            'NEAR': 'Near Protocol',
            'FIL': 'Filecoin',
            'GRT': 'The Graph',
        }
        
        # Clear existing crypto data
        cursor.execute("DELETE FROM crypto_assets")
        
        # Generate test data for 30 days
        base_date = datetime.now() - timedelta(days=30)
        
        for symbol, (min_price, max_price) in price_ranges.items():
            for day in range(30):
                current_date = base_date + timedelta(days=day)
                base_price = random.uniform(min_price, max_price)
                
                price = base_price + random.uniform(-1, 1)
                price = max(min_price, min(max_price, price))
                
                volume = int(random.uniform(1000000, 5000000))
                market_cap = int(random.uniform(1000000000, 50000000000))
                
                cursor.execute("""
                    INSERT INTO crypto_assets 
                    (symbol, name, price_usd, market_cap, volume_24h, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (symbol, asset_names[symbol], price, market_cap, volume, current_date))
        
        conn.commit()
        print(f" Populated crypto test data (450 records: 15 assets  30 days)")
        
        # Populate cache with current crypto data
        try:
            cursor.execute("""
                SELECT symbol, name, price_usd, market_cap, volume_24h, timestamp
                FROM crypto_assets
                WHERE timestamp = (SELECT MAX(timestamp) FROM crypto_assets)
            """)
            rows = cursor.fetchall()
            if rows:
                crypto_data = {}
                for row in rows:
                    symbol, name, price_usd, market_cap, volume_24h, timestamp = row
                    # Normalize with DataService
                    normalized = DataService.CRYPTO.normalize_crypto({
                        'symbol': symbol,
                        'name': name,
                        'price_usd': price_usd,
                        'market_cap': market_cap,
                        'volume_24h': volume_24h
                    })
                    crypto_data[symbol] = normalized
                
                # Update cache with latest crypto data
                if cache:
                    cache.update_crypto(crypto_data)
                    print(f" Updated cache with {len(crypto_data)} crypto assets")
        except Exception as cache_err:
            print(f"Warning: Could not populate cache with crypto data: {cache_err}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error initializing crypto assets: {e}")
        import traceback
        traceback.print_exc()

def load_initial_data_to_cache():
    """Load initial data from database into cache on app startup."""
    try:
        from database.connection import create_connection
        
        if not cache:
            print("Cache not available during initialization")
            return
        
        conn = create_connection()
        if not conn:
            print("Failed to load initial data: Database connection failed")
            return
        
        cursor = conn.cursor()
        
        # Load latest weather data into cache
        try:
            cursor.execute("""
                SELECT location, temperature, humidity, pressure, wind_speed, timestamp
                FROM weather_latest
                ORDER BY timestamp DESC
                LIMIT 50
            """)
            rows = cursor.fetchall()
            if rows:
                weather_data = {}
                for row in rows:
                    location, temp, humidity, pressure, wind, timestamp = row
                    normalized = DataService.WEATHER.normalize_weather({
                        'location_name': location,
                        'temperature': temp,
                        'humidity': humidity,
                        'pressure': pressure,
                        'wind_speed': wind
                    })
                    weather_data[location] = normalized
                
                if weather_data:
                    cache.update_weather(weather_data)
                    print(f" Loaded {len(weather_data)} weather locations into cache")
        except Exception as w_err:
            print(f"Warning: Could not load weather data into cache: {w_err}")
        
        # Load latest social trends data into cache
        try:
            cursor.execute("""
                SELECT name, source, volume, sentiment_score, timestamp
                FROM social_latest
                ORDER BY timestamp DESC
                LIMIT 100
            """)
            rows = cursor.fetchall()
            if rows:
                social_data = {}
                for row in rows:
                    name, source, volume, sentiment, timestamp = row
                    key = f"{name}_{source}"
                    normalized = DataService.SOCIAL_TRENDS.normalize_social_trend({
                        'name': name,
                        'source': source,
                        'volume': volume,
                        'sentiment_score': sentiment
                    })
                    social_data[key] = normalized
                
                if social_data:
                    cache.update_social_trends(social_data)
                    print(f" Loaded {len(social_data)} social trends into cache")
        except Exception as s_err:
            print(f"Warning: Could not load social trends into cache: {s_err}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error loading initial data to cache: {e}")
        import traceback
        traceback.print_exc()

def login_required(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('auth_token')
        if not token or not AuthManager.verify_session(token):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def no_cache(f):
    """Decorator to prevent response caching."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        if isinstance(response, tuple):
            response_obj = response[0]
        else:
            from flask import make_response
            response_obj = make_response(response)
        
        response_obj.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response_obj.headers['Pragma'] = 'no-cache'
        response_obj.headers['Expires'] = '0'
        
        if isinstance(response, tuple):
            return response_obj, response[1] if len(response) > 1 else 200
        return response_obj
    return decorated_function

@app.route('/set_theme', methods=['POST'])
@login_required
def set_theme_route():
    theme = request.json.get('theme')
    if theme in THEME_PRESETS:
        session['current_theme'] = theme
        if 'user_id' in session:
            set_user_theme(session['user_id'], theme)
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Invalid theme'}), 400

def get_db_connection():
    return create_connection()

def current_username():
    token = request.cookies.get('auth_token')
    username = AuthManager.get_username(token)
    # Only trust Flask-session fallback when it matches the active auth token.
    if not username and token and session.get('auth_token') == token:
        username = session.get('username')
    return username


def get_active_theme():
    username = current_username()
    theme = get_user_theme(username) if username else "dark_glass"
    return theme if theme in THEME_PRESETS else "dark_glass"


def get_global_menu():
    """
    Build global menu from one config source, merged with DB pages to avoid omissions.
    """
    username = current_username()
    if not username:
        return []
    try:
        modules = get_user_menu_modules(username)
        # return merge_menu_with_db_modules(MENU_ITEMS, modules)
        return MENU_ITEMS
    except Exception:
        return MENU_ITEMS


@app.context_processor
def inject_menu():
    return dict(global_menu=get_global_menu(), current_theme=get_active_theme())


def _extract_legacy_parts(rendered_html):
    head_match = re.search(r"<head[^>]*>(.*?)</head>", rendered_html, flags=re.IGNORECASE | re.DOTALL)
    body_match = re.search(r"<body[^>]*>(.*?)</body>", rendered_html, flags=re.IGNORECASE | re.DOTALL)
    title_match = re.search(r"<title[^>]*>(.*?)</title>", rendered_html, flags=re.IGNORECASE | re.DOTALL)

    head = head_match.group(1) if head_match else ""
    body = body_match.group(1) if body_match else rendered_html
    title = title_match.group(1).strip() if title_match else None

    # Keep styles/links/scripts/meta from old head, but drop title to avoid duplicates.
    head = re.sub(r"<title[^>]*>.*?</title>", "", head, flags=re.IGNORECASE | re.DOTALL)
    body = _strip_legacy_navigation(body)
    return title, head, body


def _strip_legacy_navigation(body_html):
    cleaned = body_html or ""
    patterns = [
        # Explicit nav/aside blocks.
        r"<nav\b[^>]*>.*?</nav>",
        r"<aside\b[^>]*>.*?</aside>",
        # Common header/topbar wrappers that include menu/logout controls.
        r"<(div|header)[^>]*class=[\"'][^\"']*(?:topbar|top|navbar|header)[^\"']*[\"'][^>]*>.*?(?:/menu|/menu-v2|logout\(\)|window\.location\.href='/menu').*?</\1>",
    ]
    for pattern in patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.DOTALL)

    # Remove standalone back/menu anchors and menu buttons.
    cleaned = re.sub(
        r"<a\b[^>]*href=[\"']/menu(?:-v2)?[\"'][^>]*>.*?</a>",
        "",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )
    cleaned = re.sub(
        r"<button\b[^>]*(?:onclick=[\"'][^\"']*?/menu[^\"']*[\"'])[^>]*>.*?</button>",
        "",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return cleaned


def render_legacy_template(template_source, **context):
    rendered = app.jinja_env.from_string(template_source).render(**context, request=request)
    page_title, legacy_head, page_content = _extract_legacy_parts(rendered)
    return render_template(
        "legacy_page.html",
        page_title=page_title,
        legacy_head=legacy_head,
        page_content=page_content,
    )


def build_theme_style(theme_key):
    t = THEME_PRESETS.get(theme_key, THEME_PRESETS["dark_glass"])
    c = t["colors"]
    ty = t["typography"]
    g = t["geometry"]
    
    return f"""
<style id="global-theme-vars">
:root {{
  /* Colors */
  --bg-base: {c['bg_base']};
  --bg-secondary: {c['bg_secondary']};
  --bg-panel: {c['bg_panel']};
  --bg-glass: {c['bg_glass']};
  --bg-glass-hover: {c['bg_glass_hover']};
  --accent-primary: {c['accent_primary']};
  --accent-secondary: {c['accent_secondary']};
  --accent-tertiary: {c['accent_tertiary']};
  --accent-grad: {c['accent_grad']};
  --text-primary: {c['text_primary']};
  --text-secondary: {c['text_secondary']};
  --text-tertiary: {c['text_tertiary']};
  --text-inverse: {c['text_inverse']};
  --border-subtle: {c['border_subtle']};
  --border-focus: {c['border_focus']};
  --glow-primary: {c['glow_primary']};
  --glow-secondary: {c['glow_secondary']};
  --ambient-primary: {c['ambient_primary']};
  --ambient-secondary: {c['ambient_secondary']};

  /* Typography */
  --font-primary: {ty['font_primary']};
  --font-heading: {ty['font_heading']};
  --font-weight-heading: {ty['font_weight_heading']};

  /* Geometry / Spacing / Radius */
  --radius-sm: {g['radius_sm']};
  --radius-md: {g['radius_md']};
  --radius-lg: {g['radius_lg']};
  --radius-xl: {g['radius_xl']};
  --radius-full: {g['radius_full']};
  --glass-blur: {g['glass_blur']};
  
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-2xl: 48px;

  /* Shadows */
  --shadow-sm: {g['shadow_sm']};
  --shadow-md: {g['shadow_md']};
  --shadow-lg: {g['shadow_lg']};
  --shadow-glow: {g['shadow_glow']};

  /* Motion */
  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-normal: 300ms cubic-bezier(0.4, 0, 0.2, 1);
  --ease-spring: cubic-bezier(0.4, 0, 0.2, 1);
}}
</style>
"""


@app.after_request
def apply_user_theme(response):
    """Inject dynamic theme CSS variables into the response HTML."""
    try:
        # Only process successful HTML responses
        if (response.content_type and 'text/html' in response.content_type and 
            response.status_code == 200 and not request.path.startswith('/api/')):
            
            html = response.get_data(as_text=True)
            if "</head>" in html and "id=\"global-theme-vars\"" not in html:
                theme_style = build_theme_style(get_active_theme())
                themed_html = html.replace("</head>", f"{theme_style}\n</head>", 1)
                response.set_data(themed_html)
                # Remove Content-Length so Flask/WSGI recalculates it
                response.headers.pop('Content-Length', None)
    except Exception as e:
        print(f"Theme injection error: {e}")
    return response


def _build_global_menu_html(path):
    sections = get_global_menu()
    parts = [
        '<div id="global-unified-menu" class="gum-root">',
        '<button class="gum-toggle" onclick="window.__gumToggle()">Menu</button>',
        '<aside class="gum-drawer" id="gumDrawer">',
        '<div class="gum-head"><strong>Navigation</strong><button class="gum-close" onclick="window.__gumToggle(false)">x</button></div>',
    ]
    for section in sections:
        parts.append(f'<div class="gum-section-title">{html_escape.escape(section.get("section", "Section"))}</div>')
        for item in section.get("items", []):
            url = item.get("url") or "#"
            name = item.get("name") or url
            active = " gum-active" if (path == url or path.startswith(url + "/")) else ""
            parts.append(
                f'<a class="gum-link{active}" href="{html_escape.escape(url)}">{html_escape.escape(name)}</a>'
            )
    parts.append("</aside></div>")
    parts.append(
        """
<style id="global-unified-menu-style">
.gum-root{position:fixed;top:14px;left:14px;z-index:9999}
.gum-toggle{background:var(--theme-accent,#853953);color:#fff;border:none;border-radius:10px;padding:9px 12px;cursor:pointer;box-shadow:0 8px 20px rgba(0,0,0,.2)}
.gum-drawer{position:fixed;left:14px;top:54px;bottom:14px;width:280px;overflow:auto;display:none;padding:12px;border-radius:12px;background:var(--theme-surface,#fff);border:1px solid var(--theme-line,#dbe4f2);box-shadow:0 12px 32px rgba(0,0,0,.2)}
.gum-drawer.open{display:block}
.gum-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.gum-close{border:1px solid var(--theme-line,#dbe4f2);background:transparent;border-radius:8px;padding:4px 8px;cursor:pointer}
.gum-section-title{margin:12px 0 6px 0;font-size:12px;font-weight:700;color:var(--theme-muted,#5f7288);text-transform:uppercase;letter-spacing:.4px}
.gum-link{display:block;text-decoration:none;padding:8px 10px;border-radius:8px;color:var(--theme-text,#1f2d3d);font-size:13px}
.gum-link:hover{background:var(--theme-surface-alt,#f5f8ff)}
.gum-link.gum-active{background:color-mix(in srgb, var(--theme-accent,#853953) 16%, transparent);color:var(--theme-accent,#853953);font-weight:700}
</style>
<script id="global-unified-menu-script">
window.__gumToggle = function(force){
  var d = document.getElementById('gumDrawer');
  if(!d) return;
  if(typeof force === 'boolean'){
    d.classList.toggle('open', force);
  } else {
    d.classList.toggle('open');
  }
};
</script>
        """
    )
    return "".join(parts)


# @app.after_request
# def inject_unified_menu(response):
#     try:
#         if not response.content_type or 'text/html' not in response.content_type or response.status_code != 200:
#             return response
#         if request.path.startswith('/api/'):
#             return response
#         if request.path == '/login' or not current_username():
#             return response
# 
#         html = response.get_data(as_text=True)
#         if 'id="global-unified-menu"' in html:
#             return response
# 
#         body_idx = html.lower().find("<body")
#         if body_idx == -1:
#             return response
#         tag_end = html.find(">", body_idx)
#         if tag_end == -1:
#             return response
# 
#         snippet = _build_global_menu_html(request.path)
#         html = html[: tag_end + 1] + snippet + html[tag_end + 1 :]
#         response.set_data(html)
#     except Exception:
#         pass
#     return response


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        username = current_username()
        if not username or not is_admin_user(username):
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'Admin access required'}), 403
            return redirect(url_for('menu'))
        return f(*args, **kwargs)
    return decorated_function


@app.before_request
def enforce_page_permissions():
    path = normalize_path(request.path)
    if path.startswith('/static'):
        return None

    public_paths = {'/login', '/api/login'}
    if path in public_paths:
        return None

    # Allow access to realtime endpoints without breaking local debugging.
    # If you're authenticated, all APIs work normally.
    # For local dev / curl testing, let realtime endpoints bypass login.
    if path.startswith('/api/realtime/'):
        return None

    token = request.cookies.get('auth_token')
    if not token or not AuthManager.verify_session(token):
        return None


    username = current_username()
    if not username:
        return None

    # Always allow session/navigation endpoints.
    unrestricted = {'/menu', '/menu-v2', '/api/user-landing-page', '/api/logout', '/ui-settings', '/api/ui-theme'}
    if path in unrestricted:
        return None

    # Admin APIs are protected by page permissions.
    if path.startswith('/api/admin'):
        can_manage_users = user_can_access_path(username, '/admin/users')
        can_manage_permissions = user_can_access_path(username, '/admin/access-control')
        can_manage_alert_settings = user_can_access_path(username, '/admin/alert-settings')
        if not (can_manage_users or can_manage_permissions or can_manage_alert_settings):
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        return None

    if not user_can_access_path(username, path):
        if path.startswith('/api/'):
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        return redirect(url_for('menu'))
    return None

# ==================== ERROR HANDLERS ====================

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    import traceback
    print(f"500 Error: {error}")
    traceback.print_exc()
    return jsonify({'success': False, 'message': f'Internal server error: {str(error)}'}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle unexpected exceptions."""
    import traceback
    print(f"Unexpected error: {e}")
    traceback.print_exc()
    return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

# ==================== LOGIN & AUTHENTICATION ====================


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Proactively ensure DB is initialized on Vercel
    if os.environ.get('VERCEL'):
        try:
            bootstrap_all()
        except Exception as e:
            print(f"Login bootstrap failed: {e}")

    if request.method == 'POST':
        return redirect(url_for('login'))
        
    """Display login page."""
    return render_template("login.html")

@app.route('/api/login', methods=['POST'])
def api_login():
    """Handle login request."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Invalid request format'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'}), 400

        if AuthManager.verify_credentials(username, password):
            token = AuthManager.create_session(username)
            # also store username in Flask session to improve server-side detection
            session.permanent = True
            session['username'] = username
            session['auth_token'] = token
            response = jsonify({'success': True, 'message': 'Login successful', 'landing_page': '/dashboard'})
            response.set_cookie('auth_token', token, httponly=True, secure=False, samesite='Lax')
            return response
        
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

# ==================== NEW MENU PAGE (V2 - REORGANIZED) ====================
# This is the new menu with better organization and design
# To use this new menu, replace MENU_PAGE with MENU_PAGE_V2 in the menu() function below
# Future: This structure supports admin feature permissions for different user roles


# ==================== MENU PAGE ====================


# ==================== MENU ROUTING ====================
# INSTRUCTIONS:
# - Current menu: /menu (using MENU_PAGE - Original design)
# - New menu:     /menu-v2 (using MENU_PAGE_V2 - Reorganized with better design)
#
# TO SWITCH TO NEW MENU:
#   1. Replace "MENU_PAGE" with "MENU_PAGE_V2" in the route below (line ~1532)
#   2. Restart the application
#
# TO REVERT TO OLD MENU:
#   1. Change "MENU_PAGE_V2" back to "MENU_PAGE" in the route
#   2. Restart the application
#
# NEW MENU FEATURES:
#   - Organized by category (Cryptocurrency, Weather, Social Media, Admin)
#   - Better visual hierarchy and grouping
#   - Designed for future admin feature permissions
#   - Cleaner, modern UI with section-based layout
#   - Ready for multi-user role management

@app.route('/menu', methods=['GET'])
@login_required
def menu():
    """Display data-driven menu based on page permissions."""
    return redirect(url_for('dashboard_standard'))


@app.route('/menu-v2', methods=['GET'])
@login_required
def menu_v2():
    """Alias to data-driven menu."""
    return redirect(url_for('dashboard_standard'))


@app.route('/ui-settings', methods=['GET'])
@login_required
def ui_settings_page():
    username = current_username()
    return render_template("ui_settings.html", username=username)


@app.route('/api/ui-theme', methods=['GET', 'POST'])
@login_required
def api_ui_theme():
    username = current_username()
    if request.method == 'GET':
        return jsonify({"success": True, "theme": get_user_theme(username)})
    data = request.get_json() or {}
    theme = data.get("theme", "ocean")
    if theme not in THEME_PRESETS:
        return jsonify({"success": False, "message": "Invalid theme"}), 400
    ok = set_user_theme(username, theme)
    return jsonify({"success": bool(ok), "theme": theme})


@app.route('/admin/access-control', methods=['GET'])
@login_required
def admin_access_control_page():
    username = current_username()
    return render_template("admin_access_control.html")


@app.route('/api/admin/access-config', methods=['GET'])
@login_required
def api_admin_access_config():
    username = request.args.get('username')
    modules = get_modules_with_pages()
    users = list_users()
    allowed = get_user_allowed_page_keys(username) if username else []
    return jsonify({
        'success': True,
        'modules': modules,
        'users': users,
        'allowed_page_keys': allowed,
    })


@app.route('/admin/users', methods=['GET'])
@login_required
def admin_users_page():
    username = current_username()
    return render_template("admin_users.html", username=username)


@app.route('/admin/alert-settings', methods=['GET'])
@login_required
def admin_alert_settings_page():
    username = current_username()
    return render_template("admin_alert_settings.html", username=username)


@app.route('/api/admin/users', methods=['POST'])
@login_required
def api_admin_create_user():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    is_admin_flag = bool(data.get('is_admin', False))
    if not username or not password:
        return jsonify({'success': False, 'message': 'username/password required'}), 400
    ok = create_user(username, password, is_admin=is_admin_flag, is_active=True)
    if not ok:
        return jsonify({'success': False, 'message': 'failed to create user'}), 400
    # Default permissions: non-admin gets none, admin gets all pages.
    if is_admin_flag:
        all_page_keys = []
        for module in get_modules_with_pages():
            for page in module.get('pages', []):
                all_page_keys.append(page['page_key'])
        set_user_allowed_pages(username, all_page_keys)
    return jsonify({'success': True})


@app.route('/api/admin/users/<username>', methods=['PATCH'])
@login_required
def api_admin_update_user(username):
    data = request.get_json() or {}
    ok = update_user(
        username=username,
        is_admin=data.get('is_admin'),
        is_active=data.get('is_active'),
    )
    return jsonify({'success': bool(ok)})


@app.route('/api/admin/users/<username>/password', methods=['POST'])
@login_required
def api_admin_reset_password(username):
    data = request.get_json() or {}
    password = data.get('password') or ''
    if not password:
        return jsonify({'success': False, 'message': 'password required'}), 400
    ok = reset_user_password(username, password)
    return jsonify({'success': bool(ok)})


@app.route('/api/admin/users/<username>/permissions', methods=['PUT'])
@login_required
def api_admin_set_permissions(username):
    data = request.get_json() or {}
    allowed_page_keys = data.get('allowed_page_keys') or []
    ok = set_user_allowed_pages(username, allowed_page_keys)
    return jsonify({'success': bool(ok)})


# API: list/create/delete alerts
@app.route('/api/crypto-alerts', methods=['GET','POST'])
@login_required
def api_crypto_alerts():
    from database.alert_models import (
        evaluate_crypto_alerts,
        get_alerts,
        get_latest_price,
        get_price_history,
        insert_alert,
    )
    if request.method == 'GET':
        # Refresh alert state on each read so UI always reflects current conditions.
        evaluate_crypto_alerts(trigger_source='refresh', dispatch_notifications=False)
        alerts = get_alerts()
        # enrich alerts with latest price and small history
        enriched = []
        for a in alerts:
            lp = get_latest_price(a['symbol'])
            history = get_price_history(a['symbol'], limit=30)
            enriched.append({
                **a,
                'current_price': lp['price_usd'] if lp else None,
                'price_timestamp': lp['timestamp'] if lp else None,
                'history': history
            })
        return jsonify(enriched)

    # POST - create
    data = request.get_json() or {}
    symbol = data.get('symbol')
    condition = data.get('condition')
    threshold = data.get('threshold')
    notify = data.get('notify_method','console')
    alert_mode = data.get('alert_mode', 'standard')
    custom_metric = data.get('custom_metric')
    custom_config = data.get('custom_config') or {}
    cooldown_minutes = data.get('cooldown_minutes', 15)
    if not symbol or not condition or threshold is None:
        return jsonify({'success': False, 'message': 'missing fields'}), 400
    ok = insert_alert(
        symbol,
        condition,
        threshold,
        is_active=True,
        notify_method=notify,
        alert_mode=alert_mode,
        custom_metric=custom_metric,
        custom_config=custom_config,
        cooldown_minutes=cooldown_minutes,
    )
    return jsonify({'success': ok})

@app.route('/api/crypto-alerts/<int:alert_id>', methods=['DELETE'])
@login_required
def api_delete_alert(alert_id):
    from database.alert_models import delete_alert
    ok = delete_alert(alert_id)
    return jsonify({'success': ok})


@app.route('/api/crypto-alerts/events', methods=['GET'])
@login_required
def api_crypto_alert_events():
    from database.alert_models import get_crypto_alert_events
    limit = request.args.get('limit', 100, type=int)
    return jsonify(get_crypto_alert_events(limit=limit))


@app.route('/api/admin/alert-channels', methods=['GET', 'POST'])
@login_required
@admin_required
def api_admin_alert_channels():
    from database.alert_models import get_notification_channels, upsert_notification_channel
    module_key = request.args.get('module_key')
    if request.method == 'GET':
        return jsonify(get_notification_channels(module_key=module_key))

    data = request.get_json() or {}
    channel_key = data.get('channel_key')
    channel_type = data.get('channel_type')
    config = data.get('config') or {}
    is_active = bool(data.get('is_active', True))
    module_key = data.get('module_key', 'all')
    if not channel_key or not channel_type:
        return jsonify({'success': False, 'message': 'channel_key and channel_type are required'}), 400

    ok = upsert_notification_channel(
        channel_key=channel_key,
        channel_type=channel_type,
        is_active=is_active,
        config=config,
        module_key=module_key,
    )
    return jsonify({'success': ok})


# ==================== WEATHER ALERTS API ====================

@app.route('/api/weather-alerts', methods=['GET','POST'])
@login_required
def api_weather_alerts():
    from database.alert_models import evaluate_weather_alerts, get_weather_alerts, insert_weather_alert
    if request.method == 'GET':
        evaluations = evaluate_weather_alerts(trigger_source='refresh', dispatch_notifications=False)
        alerts = get_weather_alerts()
        ev_map = {e.get('id'): e for e in evaluations}
        for a in alerts:
            ev = ev_map.get(a.get('id'))
            if ev:
                a['current_metric_value'] = ev.get('current_metric_value')
                a['state_message'] = ev.get('state_message')
                a['in_cooldown'] = ev.get('in_cooldown')
        return jsonify(alerts)

    # POST - create
    data = request.get_json() or {}
    location_name = data.get('location_name')
    alert_type = data.get('alert_type')
    condition = data.get('condition')
    threshold = data.get('threshold')
    metric_type = data.get('metric_type')
    notify = data.get('notify_method','console')
    cooldown_minutes = data.get('cooldown_minutes', 15)
    alert_mode = data.get('alert_mode', 'standard')
    custom_config = data.get('custom_config') or {}
    if not location_name or not condition or threshold is None or not metric_type:
        return jsonify({'success': False, 'message': 'missing fields'}), 400
    ok = insert_weather_alert(
        location_name,
        alert_type,
        condition,
        threshold,
        metric_type,
        is_active=True,
        notify_method=notify,
        alert_mode=alert_mode,
        custom_config=custom_config,
        cooldown_minutes=cooldown_minutes,
    )
    if ok:
        return jsonify({'success': True, 'message': 'Alert created'})
    return jsonify({'success': False, 'message': 'Failed to create alert'}), 500


@app.route('/api/weather-alerts/<int:alert_id>', methods=['DELETE'])
@login_required
def api_delete_weather_alert(alert_id):
    from database.alert_models import delete_weather_alert
    ok = delete_weather_alert(alert_id)
    return jsonify({'success': ok})


# ==================== SOCIAL TREND ALERTS API ====================

@app.route('/api/social-trend-alerts', methods=['GET','POST'])
@login_required
def api_social_trend_alerts():
    from database.alert_models import evaluate_social_trend_alerts, get_social_trend_alerts, insert_social_trend_alert
    if request.method == 'GET':
        evaluations = evaluate_social_trend_alerts(trigger_source='refresh', dispatch_notifications=False)
        alerts = get_social_trend_alerts()
        ev_map = {e.get('id'): e for e in evaluations}
        for a in alerts:
            ev = ev_map.get(a.get('id'))
            if ev:
                a['current_metric_value'] = ev.get('current_metric_value')
                a['state_message'] = ev.get('state_message')
                a['in_cooldown'] = ev.get('in_cooldown')
        return jsonify(alerts)

    # POST - create
    data = request.get_json() or {}
    trend_name = data.get('trend_name')
    source_platform = data.get('source_platform')
    alert_type = data.get('alert_type')
    condition = data.get('condition')
    threshold = data.get('threshold')
    metric_type = data.get('metric_type')
    notify = data.get('notify_method','console')
    cooldown_minutes = data.get('cooldown_minutes', 15)
    alert_mode = data.get('alert_mode', 'standard')
    custom_config = data.get('custom_config') or {}
    if not trend_name or not source_platform or condition is None or threshold is None or not metric_type:
        return jsonify({'success': False, 'message': 'missing fields'}), 400
    ok = insert_social_trend_alert(
        trend_name,
        source_platform,
        alert_type,
        condition,
        threshold,
        metric_type,
        is_active=True,
        notify_method=notify,
        alert_mode=alert_mode,
        custom_config=custom_config,
        cooldown_minutes=cooldown_minutes,
    )
    if ok:
        return jsonify({'success': True, 'message': 'Alert created'})
    return jsonify({'success': False, 'message': 'Failed to create alert'}), 500


@app.route('/api/social-trend-alerts/<int:alert_id>', methods=['DELETE'])
@login_required
def api_delete_social_trend_alert(alert_id):
    from database.alert_models import delete_social_trend_alert
    ok = delete_social_trend_alert(alert_id)
    return jsonify({'success': ok})




@app.route('/crypto-alerts')
@login_required
def crypto_alerts_page():
    """Render the Crypto Alerts management page."""
    username = AuthManager.get_username(request.cookies.get('auth_token'))
    return render_template("crypto_alerts.html")

# ==================== WEATHER ALERTS PAGE ====================

@app.route('/weather-alerts')
@login_required
def weather_alerts_page():
    """Render the Weather Alerts management page."""
    username = AuthManager.get_username(request.cookies.get('auth_token'))
    return render_template("weather_alerts.html")


# ==================== SOCIAL TREND ALERTS PAGE ====================

@app.route('/social-trend-alerts')
@login_required
def social_trend_alerts_page():
    """Render the Social Trend Alerts management page."""
    username = AuthManager.get_username(request.cookies.get('auth_token'))
    return render_template("social_trend_alerts.html")


# ==================== ASSET MANAGEMENT ====================


@app.route('/asset-management', methods=['GET'])
@login_required
def asset_management():
    # Ensure database is seeded
    if os.environ.get('VERCEL'):
        try:
            bootstrap_all()
        except Exception as e:
            print(f"Management bootstrap error: {e}")
            
    """Display asset management page."""
    return render_template("asset_management.html")

# ==================== ASSET API ENDPOINTS ====================

@app.route('/api/assets', methods=['GET'])
@login_required
def get_assets():
    """Get all preferred assets."""
    assets = PreferredAssetsManager.get_all_assets()
    return jsonify({'success': True, 'assets': assets})

@app.route('/api/assets', methods=['POST'])
@login_required
def add_asset():
    """Add a new preferred asset."""
    data = request.get_json()
    symbol = data.get('symbol', '').strip().upper()
    name = data.get('name', '').strip()

    if not symbol or not name:
        return jsonify({'success': False, 'message': 'Symbol and name are required'}), 400

    success, message = PreferredAssetsManager.add_asset(symbol, name)
    return jsonify({'success': success, 'message': message}), 200 if success else 400

@app.route('/api/assets/<int:asset_id>', methods=['DELETE'])
@login_required
def delete_asset(asset_id):
    """Delete a preferred asset."""
    success, message = PreferredAssetsManager.delete_asset(asset_id)
    return jsonify({'success': success, 'message': message}), 200 if success else 400

@app.route('/api/preferred-assets', methods=['GET'])
@login_required
def get_preferred_assets():
    """Get all preferred assets for dropdown selection."""
    assets = PreferredAssetsManager.get_all_assets()
    return jsonify(assets)

@app.route('/api/logout', methods=['POST'])
def api_logout():
    """Handle logout."""
    token = request.cookies.get('auth_token')
    AuthManager.logout(token)
    session.pop('username', None)
    session.pop('auth_token', None)
    session.clear()
    response = jsonify({'success': True})
    response.delete_cookie('auth_token')
    return response


# ==================== USER LANDING PAGE ====================

@app.route('/api/user-landing-page', methods=['GET'])
@login_required
def api_user_landing_page():
    """Get the appropriate landing page for the current user based on their session/privileges.
    
    Returns:
        - '/menu-v2' for admin users
        - '/menu' for other users (or custom configured page)
        - Can be extended for role-based custom pages
    """
    token = request.cookies.get('auth_token')
    username = AuthManager.get_username(token)
    
    if not username:
        return jsonify({'landing_page': '/dashboard', 'username': None}), 401
    
    landing_page = get_first_allowed_route(username)
    return jsonify({
        'success': True,
        'landing_page': landing_page,
        'username': username
    })

# ==================== SYNC DATA ====================

@app.route('/api/sync-data', methods=['GET'])
@login_required
def sync_data():
    """Read-only API: return latest crypto snapshot (does NOT trigger fetch)."""
    try:
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT symbol, name, price_usd, market_cap, volume_24h, last_updated
            FROM crypto_latest
            ORDER BY last_updated DESC, symbol ASC
        """)
        rows = cursor.fetchall()
        
        # Get the most recent timestamp
        timestamp = None
        if rows:
            timestamp = rows[0].get('last_updated')
        
        cursor.close()
        connection.close()
        
        return jsonify({'success': True, 'data': rows, 'last_updated': timestamp})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


def _compute_freshness_status(last_sync, interval_minutes):
    now = datetime.now()
    stale_after = int(interval_minutes) * 2 + 1
    if not last_sync:
        return {
            'status': 'no_data',
            'age_minutes': None,
            'stale_after_minutes': stale_after,
            'message': 'No sync data yet'
        }

    age_minutes = max(int((now - last_sync).total_seconds() // 60), 0)
    status = 'fresh' if age_minutes <= stale_after else 'stale'
    return {
        'status': status,
        'age_minutes': age_minutes,
        'stale_after_minutes': stale_after,
        'message': 'Fresh' if status == 'fresh' else 'Stale pipeline detected'
    }


@app.route('/api/data-freshness', methods=['GET'])
@login_required
def api_data_freshness():
    """Return last successful sync times and stale/fresh status by module."""
    connection = create_connection()
    if not connection:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500

    cursor = connection.cursor()
    try:
        checks = [
            {
                'module': 'Crypto',
                'table': 'crypto_latest',
                'timestamp_col': 'last_updated',
                'interval_minutes': SCRAPE_INTERVAL_MINUTES,
            },
            {
                'module': 'Weather',
                'table': 'weather_latest',
                'timestamp_col': 'last_updated',
                'interval_minutes': WEATHER_SYNC_INTERVAL_MINUTES,
            },
            {
                'module': 'Social',
                'table': 'social_latest',
                'timestamp_col': 'data_collected_at',
                'interval_minutes': SOCIAL_SYNC_INTERVAL_MINUTES,
            },
        ]

        modules = []
        stale_count = 0
        for item in checks:
            cursor.execute(f"SELECT MAX({item['timestamp_col']}) FROM {item['table']}")
            last_sync = cursor.fetchone()[0]
            cursor.execute(f"SELECT COUNT(*) FROM {item['table']}")
            row_count = cursor.fetchone()[0]
            freshness = _compute_freshness_status(last_sync, item['interval_minutes'])
            if freshness['status'] == 'stale':
                stale_count += 1

            modules.append({
                'module': item['module'],
                'table': item['table'],
                'row_count': int(row_count or 0),
                'expected_interval_minutes': int(item['interval_minutes']),
                'last_sync': last_sync.isoformat() if last_sync else None,
                **freshness
            })

        return jsonify({
            'success': True,
            'generated_at': datetime.now().isoformat(),
            'stale_count': stale_count,
            'modules': modules,
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        connection.close()


@app.route('/data-freshness-monitor', methods=['GET'])
@login_required
def data_freshness_monitor_page():
    """Render pipeline data freshness monitor."""
    return render_template("data_freshness_monitor.html")

# ==================== DASHBOARD ROUTES ====================



@app.route('/')
def welcome():
    """Public landing page."""
    token = request.cookies.get('auth_token')
    username = AuthManager.get_username(token) if token else None
    return render_template("welcome.html", username=username)

@app.route('/dashboard')
@login_required
@no_cache
def dashboard_standard():

    try:
        vis = get_visualizer()

        # Load symbols from preferred_assets database table (up to 10)
        assets_manager = PreferredAssetsManager()
        assets = assets_manager.get_all_assets()
        symbols = [asset['symbol'] for asset in assets[:10]] if assets else None

        fig = vis.create_performance_comparison_chart(symbols=symbols, hours_back=24)

        if fig:

            fig.update_layout(
            height=300,
            margin=dict(l=10, r=10, t=40, b=10),
            bargap=0.5
            )

            crypto_chart = fig.to_html(
            full_html=False,
            default_width="100%",
            default_height="300px"
            )
        else:
            crypto_chart = "<div>No crypto data available</div>"

    except Exception as e:
        crypto_chart = f"<div style='color:red'>Chart error: {e}</div>"

    sentiment_chart = """
    <div style='height:260px;display:flex;align-items:center;justify-content:center;color:#666'>
        Sentiment module coming soon
    </div>
    """

    # Get weather location from predefined locations
    weather_city = "Unknown location"
    try:
        from scraper.weather import get_predefined_locations
        locations = get_predefined_locations()
        if locations and len(locations) > 0:
            weather_city = locations[0].get('name', 'Unknown location')
    except Exception as e:
        print(f"Error fetching weather location: {e}")

    return render_template(
        "home_dashboard.html",
        crypto_chart=crypto_chart,
        sentiment_chart=sentiment_chart,
        weather_city=weather_city
    )

@app.route('/advanced-dashboard')
@login_required
def advanced_dashboard():
    """Legacy advanced route redirected to canonical advanced dashboard route."""
    return redirect(url_for('advanced_crypto_dashboard'))

def get_dashboard_html():
    """Get dashboard HTML template."""
    return render_template("dashboard.html")

def get_advanced_dashboard_html():
    """Get advanced dashboard HTML template."""
    return render_template("advanced_dashboard.html")

# ==================== API ENDPOINTS ====================

@app.route('/api/dashboard-data')
@login_required
@no_cache
def get_dashboard_data():
    """Get dashboard data - Simplified Version."""
    try:
        connection = create_connection()
        if not connection:
            return jsonify({
                'metrics': {
                    'Total Assets': '0',
                    'Market Cap': '$0',
                    'Total Volume': '$0',
                    'Avg Price': '$0'
                },
                'charts': [],
                'alerts': [{'level': 'low', 'message': 'Database connection failed'}]
            })
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT symbol, name, price_usd, market_cap, volume_24h, timestamp 
            FROM crypto_assets 
            WHERE timestamp >= NOW() - INTERVAL '24 HOURS'
            ORDER BY timestamp DESC 
        """)
        latest = cursor.fetchall()
        
        count = len(latest)
        timestamp = None
        if latest:
            timestamp = latest[0].get('timestamp')

        # Compose simple metrics from latest snapshot
        total_market_cap = sum([row.get('market_cap') or 0 for row in latest])
        total_volume = sum([row.get('volume_24h') or 0 for row in latest])
        avg_price = (sum([float(row.get('price_usd') or 0) for row in latest]) / count) if count else 0

        metrics = {
            'Total Assets': str(count),
            'Market Cap': f'${total_market_cap:,}',
            'Total Volume': f'${total_volume:,}',
            'Avg Price': f'${avg_price:.2f}'
        }

        alerts = [
            {'level': 'low', 'message': 'System operating normally'},
            {'level': 'low', 'message': f'{count} assets in latest snapshot'}
        ]
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'metrics': metrics,
            'charts': [],
            'alerts': alerts,
            'last_updated': timestamp
        })
    except Exception as e:
        print(f"Dashboard error: {e}")
        return jsonify({
            'metrics': {
                'Total Assets': '0',
                'Market Cap': '$0',
                'Total Volume': '$0',
                'Avg Price': '$0'
            },
            'charts': [],
            'alerts': [{'level': 'low', 'message': 'No data available'}]
        })


@app.route('/api/signal-fusion')
@login_required
@no_cache
def api_signal_fusion():
    """Read-only Signal Fusion Index API."""
    try:
        hours = int(request.args.get('hours', 24))
    except Exception:
        hours = 24
    if hours <= 0:
        hours = 24

    rows = get_signal_fusion_index(hours=hours)
    latest_confidence = rows[-1].get('confidence_level') if rows else 'Low'

    points = [
        {
            'timestamp': row.get('timestamp').isoformat() if row.get('timestamp') else None,
            'fusion_score': float(row.get('fusion_score') or 0),
        }
        for row in rows
    ]

    return jsonify(
        {
            'hours': hours,
            'series': points,
            'latest_confidence_level': latest_confidence,
        }
    )


@app.route('/signal-fusion-report')
@login_required
def signal_fusion_report():
    """Dedicated Signal Fusion Index report page (separate from existing reports)."""
    return render_template("signal_fusion_report.html")

@app.route('/api/advanced-dashboard-data')
@login_required
def get_advanced_dashboard_data():
    """Get advanced dashboard data - Simplified Version."""
    try:
        connection = create_connection()
        if not connection:
            return jsonify({
                'analytics': {},
                'charts': [],
                'insights': [{'title': 'Error', 'description': 'Database connection failed'}]
            })
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT symbol, name, price_usd, market_cap, volume_24h, timestamp 
            FROM crypto_assets 
            WHERE timestamp >= NOW() - INTERVAL '24 HOURS'
            ORDER BY timestamp DESC
        """)
        latest = cursor.fetchall()
        
        count = len(latest)
        timestamp = None
        if latest:
            timestamp = latest[0].get('timestamp')
        
        analytics = {
            'Market Cap': {'value': '$234.5B', 'icon': ''},
            '24h Volume': {'value': '$156.2B', 'icon': ''},
            'Assets': {'value': str(count), 'icon': ''},
            '24h Change': {'value': '+3.45%', 'icon': ''}
        }
        
        insights = [
            {'title': ' System Status', 'description': 'All systems operating normally'},
            {'title': ' Data Status', 'description': f'Latest snapshot contains {count} cryptocurrency records'},
            {'title': ' Auto-Refresh', 'description': 'Dashboard updates every 10 minutes'}
        ]
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'analytics': analytics,
            'charts': [],
            'insights': insights,
            'last_updated': timestamp
        })
    except Exception as e:
        print(f"Advanced dashboard error: {e}")
        return jsonify({
            'analytics': {},
            'charts': [],
            'insights': [{'title': 'Error', 'description': 'Unable to load data'}]
        })

# ==================== ASSET SELECTION DASHBOARD ====================

@app.route('/asset-dashboard')
@login_required
def asset_dashboard():
    # Ensure database is seeded even if login page was bypassed
    if os.environ.get('VERCEL'):
        try:
            bootstrap_all()
        except Exception as e:
            print(f"Dashboard bootstrap error: {e}")

    """Display cryptocurrency asset analytics dashboard."""
    return render_template("asset_dashboard.html")

def get_asset_dashboard_html():
    """Get asset dashboard HTML with interactive asset selection."""
    return render_template("asset_dashboard.html")

@app.route('/api/asset-list')
@login_required
@no_cache
def get_asset_list():
    """Get list of available assets."""
    try:
        from database.connection import create_connection
        from database.preferred_assets import PreferredAssetsManager
        
        assets = PreferredAssetsManager.get_all_assets()
        
        return jsonify({
            'assets': [{'symbol': a['symbol'], 'name': a['name']} for a in assets]
        })
    except Exception as e:
        print(f"Error getting asset list: {e}")
        return jsonify({'assets': []})

@app.route('/api/asset-data/<symbol>')
@login_required
@no_cache
def get_asset_data(symbol):
    """Get asset data with charts."""
    try:
        from database.connection import create_connection
        from visualization.charts import CryptoVisualizer
        import json
        
        conn = create_connection()
        if not conn:
            return jsonify({'charts': [], 'metrics': {}, 'assetInfo': {}})
        
        cursor = conn.cursor()
        
        # Get asset info
        cursor.execute("SELECT name FROM preferred_assets WHERE symbol = %s", (symbol,))
        asset = cursor.fetchone()
        asset_name = asset[0] if asset else symbol
        
        # Get recent price data
        cursor.execute("""
            SELECT price_usd FROM crypto_assets 
            WHERE symbol = %s 
            ORDER BY timestamp DESC 
            LIMIT 1
        """, (symbol,))
        price_row = cursor.fetchone()
        current_price = f"${price_row[0]:.2f}" if price_row else "N/A"
        
        # Get data for charts (last 24 hours)
        cursor.execute("""
            SELECT timestamp, price_usd, market_cap, volume_24h 
            FROM crypto_assets 
            WHERE symbol = %s AND timestamp >= NOW() - INTERVAL '24 HOURS'
            ORDER BY timestamp ASC
        """, (symbol,))
        
        data_rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not data_rows:
            return jsonify({'charts': [], 'metrics': {}, 'assetInfo': {
                'name': asset_name,
                'symbol': symbol,
                'price': current_price
            }})
        
        # Prepare data for charts
        reversed_rows = list(reversed(data_rows))
        timestamps = [str(row[0]) for row in reversed_rows]
        prices = [float(row[1]) for row in reversed_rows]
        market_caps = [float(row[2]) if row[2] else 0 for row in reversed_rows]
        volumes = [float(row[3]) if row[3] else 0 for row in reversed_rows]
        
        charts = []
        
        # Price chart
        if prices:
            price_trace = {
                'x': timestamps,
                'y': prices,
                'type': 'scatter',
                'mode': 'lines',
                'name': f'{symbol} Price',
                'line': {'color': '#853953', 'width': 3}
            }
            charts.append({
                'title': f'{symbol} Price Trend',
                'data': [price_trace],
                'layout': {
                    'hovermode': 'x unified',
                    'margin': {'l': 50, 'r': 50, 't': 30, 'b': 30},
                    'plot_bgcolor': '#F3F4F4',
                    'paper_bgcolor': '#F3F4F4',
                    'font': {'color': '#2C2C2C'},
                    'xaxis': {'title': 'Time', 'gridcolor': 'rgba(44,44,44,0.1)'},
                    'yaxis': {'title': f'Price (USD)', 'gridcolor': 'rgba(44,44,44,0.1)'}
                }
            })
        
        # Volume chart
        if volumes:
            volume_trace = {
                'x': timestamps,
                'y': volumes,
                'type': 'bar',
                'name': f'{symbol} Volume',
                'marker': {'color': '#612D53', 'opacity': 0.88}
            }
            charts.append({
                'title': f'{symbol} Trading Volume',
                'data': [volume_trace],
                'layout': {
                    'hovermode': 'x unified',
                    'margin': {'l': 50, 'r': 50, 't': 30, 'b': 30},
                    'plot_bgcolor': '#F3F4F4',
                    'paper_bgcolor': '#F3F4F4',
                    'font': {'color': '#2C2C2C'},
                    'xaxis': {'title': 'Time', 'gridcolor': 'rgba(44,44,44,0.1)'},
                    'yaxis': {'title': 'Volume', 'gridcolor': 'rgba(44,44,44,0.1)'}
                }
            })
        
        # Market Cap chart
        if market_caps and any(market_caps):
            market_cap_trace = {
                'x': timestamps,
                'y': market_caps,
                'type': 'scatter',
                'mode': 'lines+markers',
                'name': f'{symbol} Market Cap',
                'line': {'color': '#2C2C2C', 'width': 3},
                'marker': {'size': 5, 'color': '#853953'}
            }
            charts.append({
                'title': f'{symbol} Market Cap',
                'data': [market_cap_trace],
                'layout': {
                    'hovermode': 'x unified',
                    'margin': {'l': 50, 'r': 50, 't': 30, 'b': 30},
                    'plot_bgcolor': '#F3F4F4',
                    'paper_bgcolor': '#F3F4F4',
                    'font': {'color': '#2C2C2C'},
                    'xaxis': {'title': 'Time', 'gridcolor': 'rgba(44,44,44,0.1)'},
                    'yaxis': {'title': 'Market Cap (USD)', 'gridcolor': 'rgba(44,44,44,0.1)'}
                }
            })
        
        # Calculate metrics
        metrics = {
            'Current Price': current_price,
            'Avg Price': f"${sum(prices)/len(prices):.2f}" if prices else "N/A",
            'High': f"${max(prices):.2f}" if prices else "N/A",
            'Low': f"${min(prices):.2f}" if prices else "N/A",
            'Data Points': str(len(prices))
        }
        
        return jsonify({
            'assetInfo': {
                'name': asset_name,
                'symbol': symbol,
                'price': current_price
            },
            'metrics': metrics,
            'charts': charts
        })
    except Exception as e:
        print(f"Error getting asset data: {e}")
        return jsonify({'charts': [], 'metrics': {}, 'assetInfo': {}})

@app.route('/advanced-crypto-dashboard')
@login_required
def advanced_crypto_dashboard():
    """Display advanced crypto analytics dashboard with asset selection."""
    return render_template("advanced_crypto_dashboard.html")

def get_advanced_crypto_dashboard_html():
    """Get advanced crypto dashboard HTML with interactive asset selection."""
    return render_template("advanced_crypto_dashboard.html")

@app.route('/api/advanced-asset-data/<symbol>')
@login_required
@no_cache
def get_advanced_asset_data(symbol):
    """Get advanced analytics data for an asset."""
    try:
        from database.connection import create_connection
        import json
        
        conn = create_connection()
        if not conn:
            return jsonify({'charts': [], 'metrics': {}, 'assetInfo': {}})
        
        cursor = conn.cursor()
        
        # Get asset info
        cursor.execute("SELECT name FROM preferred_assets WHERE symbol = %s", (symbol,))
        asset = cursor.fetchone()
        asset_name = asset[0] if asset else symbol
        
        # Get recent price data
        cursor.execute("""
            SELECT price_usd FROM crypto_assets 
            WHERE symbol = %s 
            ORDER BY timestamp DESC 
            LIMIT 1
        """, (symbol,))
        price_row = cursor.fetchone()
        current_price = f"${price_row[0]:.2f}" if price_row else "N/A"
        
        # Get full data for analytics
        cursor.execute("""
            SELECT timestamp, price_usd, market_cap, volume_24h 
            FROM crypto_assets 
            WHERE symbol = %s 
            ORDER BY timestamp ASC
        """, (symbol,))
        
        data_rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not data_rows:
            return jsonify({'charts': [], 'metrics': {}, 'assetInfo': {
                'name': asset_name,
                'symbol': symbol,
                'price': current_price
            }})
        
        # Prepare data
        timestamps = [row[0] for row in data_rows]
        prices = [float(row[1]) for row in data_rows]
        market_caps = [float(row[2]) if row[2] else 0 for row in data_rows]
        volumes = [float(row[3]) if row[3] else 0 for row in data_rows]
        
        charts = []
        
        # Advanced Price Trend with Filled Area
        if prices:
            price_trace = {
                'x': timestamps,
                'y': prices,
                'type': 'scatter',
                'mode': 'lines',
                'name': f'{symbol} Price',
                'fill': 'tozeroy',
                'line': {'color': '#4dd0e1', 'width': 3},
                'fillcolor': 'rgba(77, 208, 225, 0.2)'
            }
            charts.append({
                'title': f'{symbol} Price Trend (Advanced)',
                'data': [price_trace],
                'layout': {
                    'hovermode': 'x unified',
                    'margin': {'l': 50, 'r': 50, 't': 30, 'b': 30},
                    'plot_bgcolor': 'rgba(255,255,255,0.05)',
                    'paper_bgcolor': 'transparent',
                    'font': {'color': 'white'},
                    'xaxis': {'title': 'Time', 'titlefont': {'color': 'white'}, 'tickfont': {'color': 'white'}},
                    'yaxis': {'title': f'Price (USD)', 'titlefont': {'color': 'white'}, 'tickfont': {'color': 'white'}}
                }
            })
        
        # Volume with Color Gradient
        if volumes:
            volume_trace = {
                'x': timestamps,
                'y': volumes,
                'type': 'bar',
                'name': f'{symbol} Volume',
                'marker': {'color': volumes, 'colorscale': 'Viridis', 'showscale': True}
            }
            charts.append({
                'title': f'{symbol} Trading Volume (Heatmap)',
                'data': [volume_trace],
                'layout': {
                    'hovermode': 'x unified',
                    'margin': {'l': 50, 'r': 50, 't': 30, 'b': 30},
                    'plot_bgcolor': 'rgba(255,255,255,0.05)',
                    'paper_bgcolor': 'transparent',
                    'font': {'color': 'white'},
                    'xaxis': {'title': 'Time', 'titlefont': {'color': 'white'}, 'tickfont': {'color': 'white'}},
                    'yaxis': {'title': 'Volume', 'titlefont': {'color': 'white'}, 'tickfont': {'color': 'white'}}
                }
            })
        
        # Market Cap with Area
        if market_caps and any(market_caps):
            market_cap_trace = {
                'x': timestamps,
                'y': market_caps,
                'type': 'scatter',
                'mode': 'lines',
                'name': f'{symbol} Market Cap',
                'fill': 'tozeroy',
                'line': {'color': '#ff7043', 'width': 2},
                'fillcolor': 'rgba(255, 112, 67, 0.2)'
            }
            charts.append({
                'title': f'{symbol} Market Cap (Area Chart)',
                'data': [market_cap_trace],
                'layout': {
                    'hovermode': 'x unified',
                    'margin': {'l': 50, 'r': 50, 't': 30, 'b': 30},
                    'plot_bgcolor': 'rgba(255,255,255,0.05)',
                    'paper_bgcolor': 'transparent',
                    'font': {'color': 'white'},
                    'xaxis': {'title': 'Time', 'titlefont': {'color': 'white'}, 'tickfont': {'color': 'white'}},
                    'yaxis': {'title': 'Market Cap (USD)', 'titlefont': {'color': 'white'}, 'tickfont': {'color': 'white'}}
                }
            })
        
        # Price Change Percentage
        if len(prices) > 1:
            price_changes = []
            for i in range(len(prices)):
                if i == 0:
                    price_changes.append(0)
                else:
                    change = ((prices[i] - prices[i-1]) / prices[i-1] * 100) if prices[i-1] != 0 else 0
                    price_changes.append(change)
            
            change_trace = {
                'x': timestamps,
                'y': price_changes,
                'type': 'scatter',
                'mode': 'lines',
                'name': f'{symbol} % Change',
                'line': {'color': '#81c784', 'width': 2},
                'fill': 'tozeroy',
                'fillcolor': 'rgba(129, 199, 132, 0.2)'
            }
            charts.append({
                'title': f'{symbol} Price Change (%)',
                'data': [change_trace],
                'layout': {
                    'hovermode': 'x unified',
                    'margin': {'l': 50, 'r': 50, 't': 30, 'b': 30},
                    'plot_bgcolor': 'rgba(255,255,255,0.05)',
                    'paper_bgcolor': 'transparent',
                    'font': {'color': 'white'},
                    'xaxis': {'title': 'Time', 'titlefont': {'color': 'white'}, 'tickfont': {'color': 'white'}},
                    'yaxis': {'title': 'Change (%)', 'titlefont': {'color': 'white'}, 'tickfont': {'color': 'white'}}
                }
            })
        
        # Calculate advanced statistics
        statistics = {
            '30-Day High': f"${max(prices):.4f}" if prices else "N/A",
            '30-Day Low': f"${min(prices):.4f}" if prices else "N/A",
            'Volatility': f"{(max(prices) - min(prices)) / (sum(prices) / len(prices) if prices else 1) * 100:.2f}%" if prices else "N/A",
            'Avg Volume': f"${sum(volumes) / len(volumes):,.0f}" if volumes else "N/A",
        }
        
        # Calculate metrics
        metrics = {
            'Current Price': current_price,
            'Avg Price': f"${sum(prices)/len(prices):.2f}" if prices else "N/A",
            'Price Range': f"${min(prices):.4f} - ${max(prices):.4f}" if prices else "N/A",
            'Data Points': str(len(prices))
        }
        
        return jsonify({
            'assetInfo': {
                'name': asset_name,
                'symbol': symbol,
                'price': current_price
            },
            'statistics': statistics,
            'metrics': metrics,
            'charts': charts
        })
    except Exception as e:
        print(f"Error getting advanced asset data: {e}")
        return jsonify({'charts': [], 'metrics': {}, 'assetInfo': {}, 'statistics': {}})

# ==================== WEATHER DASHBOARD SECTION ====================


@app.route('/weather-dashboard')
@login_required
def weather_dashboard():
    """Display new weather analytics dashboard with city selection."""
    return render_template("weather_dashboard.html")

def get_weather_analytics_dashboard_html():
    """Get weather analytics dashboard HTML with city selection."""
    return render_template("weather_analytics_dashboard.html")

@app.route('/api/weather-cities')
@login_required
@no_cache
def get_weather_cities():
    """Get list of available weather cities."""
    try:
        from database.connection import create_connection
        
        conn = create_connection()
        if not conn:
            return jsonify({'cities': []})
        
        cursor = conn.cursor()
        cursor.execute("SELECT location_name, country FROM weather_locations WHERE is_active = TRUE ORDER BY location_name")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        cities = [{'location_name': r[0], 'country': r[1]} for r in results]
        return jsonify({'cities': cities})
    except Exception as e:
        print(f"Error getting weather cities: {e}")
        return jsonify({'cities': []})

@app.route('/api/weather-city-data/<city>')
@login_required
def get_weather_city_data(city):
    """Get weather data for a specific city."""
    try:
        from database.connection import create_connection
        
        conn = create_connection()
        if not conn:
            return jsonify({'charts': [], 'metrics': {}, 'weatherInfo': {}})
        
        cursor = conn.cursor()
        
        # Get city info
        cursor.execute("SELECT country FROM weather_locations WHERE location_name = %s LIMIT 1", (city,))
        city_info = cursor.fetchone()
        country = city_info[0] if city_info else 'Unknown'
        
        # Get weather data for the city
        cursor.execute("""
            SELECT timestamp, temperature, humidity, pressure, wind_speed, weather_main, 
                   weather_description, rainfall, feels_like
            FROM weather_data 
            WHERE location_name = %s 
            ORDER BY timestamp ASC
        """, (city,))
        
        data_rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not data_rows:
            return jsonify({
                'charts': [],
                'metrics': {},
                'weatherInfo': {'city': city, 'country': country, 'current_temp': 'N/A', 'condition': 'N/A'}
            })
        
        # Process data
        timestamps = [str(row[0]) for row in data_rows]
        temperatures = [float(row[1]) for row in data_rows]
        humidity = [float(row[2]) for row in data_rows]
        pressure = [float(row[3]) for row in data_rows]
        wind_speeds = [float(row[4]) for row in data_rows]
        weather_main = [str(row[5]) for row in data_rows]
        rainfall = [float(row[7]) if row[7] else 0 for row in data_rows]
        feels_like = [float(row[8]) if row[8] else float(row[1]) for row in data_rows]
        
        current_temp = temperatures[-1] if temperatures else 0
        current_condition = weather_main[-1] if weather_main else 'N/A'
        
        charts = []
        
        # Temperature Trend
        if temperatures:
            temp_trace = {'x': timestamps, 'y': temperatures, 'type': 'scatter', 'mode': 'lines', 'name': 'Temperature', 'fill': 'tozeroy', 'line': {'color': '#ff6b6b', 'width': 2}, 'fillcolor': 'rgba(255, 107, 107, 0.2)'}
            charts.append({'title': city + ' Temperature Trend', 'data': [temp_trace], 'layout': get_plotly_dark_layout(city + ' Temperature Trend', 'Time', 'Temperature (C)')})
        
        # Humidity Trend
        if humidity:
            humidity_trace = {'x': timestamps, 'y': humidity, 'type': 'scatter', 'mode': 'lines', 'name': 'Humidity', 'fill': 'tozeroy', 'line': {'color': '#4ecdc4', 'width': 2}, 'fillcolor': 'rgba(78, 205, 196, 0.2)'}
            charts.append({'title': city + ' Humidity Trend', 'data': [humidity_trace], 'layout': get_plotly_dark_layout(city + ' Humidity Trend', 'Time', 'Humidity (%)')})
        
        # Wind Speed
        if wind_speeds:
            wind_trace = {'x': timestamps, 'y': wind_speeds, 'type': 'bar', 'name': 'Wind Speed', 'marker': {'color': '#ffd93d'}}
            charts.append({'title': city + ' Wind Speed', 'data': [wind_trace], 'layout': get_plotly_dark_layout(city + ' Wind Speed', 'Time', 'Wind Speed (m/s)')})
        
        # Rainfall
        if any(rainfall):
            rainfall_trace = {'x': timestamps, 'y': rainfall, 'type': 'bar', 'name': 'Rainfall', 'marker': {'color': '#6bcf7f'}}
            charts.append({'title': city + ' Rainfall', 'data': [rainfall_trace], 'layout': get_plotly_dark_layout(city + ' Rainfall', 'Time', 'Rainfall (mm)')})
        
        # Temperature vs Feels Like
        if temperatures and feels_like:
            temp_comparison = {'x': timestamps, 'y': temperatures, 'type': 'scatter', 'mode': 'lines', 'name': 'Actual Temp', 'line': {'color': '#ff6b6b', 'width': 2}}
            feels_trace = {'x': timestamps, 'y': feels_like, 'type': 'scatter', 'mode': 'lines', 'name': 'Feels Like', 'line': {'color': '#ff9ff3', 'width': 2, 'dash': 'dash'}}
            charts.append({'title': city + ' Temperature Comparison', 'data': [temp_comparison, feels_trace], 'layout': get_plotly_dark_layout(city + ' Temperature Comparison', 'Time', 'Temperature (C)')})
        
        # Calculate metrics
        metrics = {
            'Avg Temp': str(round(sum(temperatures)/len(temperatures), 1)) + 'C' if temperatures else 'N/A',
            'High': str(round(max(temperatures), 1)) + 'C' if temperatures else 'N/A',
            'Low': str(round(min(temperatures), 1)) + 'C' if temperatures else 'N/A',
            'Avg Humidity': str(int(sum(humidity)/len(humidity))) + '%' if humidity else 'N/A',
            'Avg Wind': str(round(sum(wind_speeds)/len(wind_speeds), 1)) + ' m/s' if wind_speeds else 'N/A',
            'Total Rainfall': str(round(sum(rainfall), 1)) + ' mm'
        }
        
        return jsonify({'weatherInfo': {'city': city, 'country': country, 'current_temp': str(round(current_temp, 1)), 'condition': current_condition}, 'metrics': metrics, 'charts': charts})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'charts': [], 'metrics': {}, 'weatherInfo': {}})

@app.route('/advanced-weather-dashboard')
@login_required
def advanced_weather_dashboard():
    """Display advanced weather analytics dashboard."""
    return render_template("advanced_weather_dashboard.html")

def get_advanced_weather_dashboard_html():
    """Get advanced weather analytics dashboard HTML."""
    return render_template("advanced_weather_dashboard.html")

@app.route('/api/advanced-weather-data/<city>')
@login_required
@no_cache
def get_advanced_weather_data(city):
    """Get advanced weather analytics for a specific city."""
    try:
        from database.connection import create_connection
        import numpy as np
        
        conn = create_connection()
        if not conn:
            return jsonify({'charts': [], 'statistics': {}})
        
        cursor = conn.cursor()
        
        # Get weather data for the city
        cursor.execute("""
            SELECT timestamp, temperature, humidity, pressure, wind_speed, weather_main, 
                   weather_description, rainfall, feels_like
            FROM weather_data 
            WHERE location_name = %s 
            ORDER BY timestamp ASC
        """, (city,))
        
        data_rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not data_rows:
            return jsonify({'charts': [], 'statistics': {}})
        
        # Process data
        timestamps = [str(row[0]) for row in data_rows]
        temperatures = [float(row[1]) for row in data_rows]
        humidity = [float(row[2]) for row in data_rows]
        pressure = [float(row[3]) for row in data_rows]
        wind_speeds = [float(row[4]) for row in data_rows]
        rainfall = [float(row[7]) if row[7] else 0 for row in data_rows]
        feels_like = [float(row[8]) if row[8] else float(row[1]) for row in data_rows]
        
        # Calculate advanced statistics
        statistics = {}
        
        if temperatures:
            temp_array = np.array(temperatures)
            statistics['Avg Temp'] = {'value': str(round(np.mean(temp_array), 1)) + 'C', 'secondary': 'Mean of ' + str(len(temperatures)) + ' readings'}
            statistics['Std Dev'] = {'value': str(round(float(np.std(temp_array)), 1)) + 'C', 'secondary': 'Temperature variability'}
            statistics['Max Temp'] = {'value': str(round(float(np.max(temp_array)), 1)) + 'C', 'secondary': 'Peak temperature'}
            statistics['Min Temp'] = {'value': str(round(float(np.min(temp_array)), 1)) + 'C', 'secondary': 'Lowest temperature'}
        
        if humidity:
            humidity_array = np.array(humidity)
            statistics['Avg Humidity'] = {'value': str(int(np.mean(humidity_array))) + '%', 'secondary': 'Average moisture'}
            statistics['Humidity Range'] = {'value': str(int(np.min(humidity_array))) + '-' + str(int(np.max(humidity_array))) + '%', 'secondary': 'Min-Max range'}
        
        if wind_speeds:
            wind_array = np.array(wind_speeds)
            statistics['Avg Wind'] = {'value': str(round(np.mean(wind_array), 1)) + ' m/s', 'secondary': 'Mean wind speed'}
            statistics['Max Wind'] = {'value': str(round(float(np.max(wind_array)), 1)) + ' m/s', 'secondary': 'Peak gust'}
        
        if any(rainfall):
            statistics['Total Rainfall'] = {'value': str(round(sum(rainfall), 1)) + ' mm', 'secondary': 'Cumulative precipitation'}
        
        # Create charts
        charts = []
        
        # 1. Temperature Distribution Histogram
        if temperatures:
            temp_hist = {'x': temperatures, 'type': 'histogram', 'name': 'Temperature', 'nbinsx': 15, 'marker': {'color': '#ff6b6b', 'opacity': 0.7}}
            charts.append({'title': 'Temperature Distribution', 'data': [temp_hist], 'layout': get_plotly_dark_layout('Temperature Distribution', 'Temperature (C)', 'Frequency', hovermode='x'), 'type': 'histogram'})
        
        # 2. Pressure Trend
        if pressure:
            pressure_trace = {'x': timestamps, 'y': pressure, 'type': 'scatter', 'mode': 'lines', 'name': 'Pressure', 'line': {'color': '#4ecdc4', 'width': 2}}
            charts.append({'title': 'Atmospheric Pressure Trend', 'data': [pressure_trace], 'layout': get_plotly_dark_layout('Atmospheric Pressure Trend', 'Time', 'Pressure (hPa)'), 'type': 'pressure'})
        
        # 3. Humidity vs Temperature Scatter
        if temperatures and humidity:
            scatter = {'x': temperatures, 'y': humidity, 'mode': 'markers', 'type': 'scatter', 'name': 'Correlation', 'marker': {'size': 6, 'color': temperatures, 'colorscale': 'Viridis', 'showscale': True, 'colorbar': {'title': 'Temp (C)'}}}
            charts.append({'title': 'Temperature-Humidity Correlation', 'data': [scatter], 'layout': get_plotly_dark_layout('Temperature-Humidity Correlation', 'Temperature (C)', 'Humidity (%)', hovermode='closest'), 'type': 'correlation'})
        
        # 4. Wind Speed Distribution
        if wind_speeds:
            wind_hist = {'x': wind_speeds, 'type': 'histogram', 'name': 'Wind Speed', 'nbinsx': 12, 'marker': {'color': '#ffd93d', 'opacity': 0.7}}
            charts.append({'title': 'Wind Speed Distribution', 'data': [wind_hist], 'layout': get_plotly_dark_layout('Wind Speed Distribution', 'Wind Speed (m/s)', 'Frequency', hovermode='x'), 'type': 'histogram'})
        
        # 5. Multi-Parameter Time Series
        if temperatures and humidity and pressure:
            temp_trace2 = {'x': timestamps, 'y': temperatures, 'type': 'scatter', 'mode': 'lines', 'name': 'Temperature', 'line': {'color': '#ff6b6b'}, 'yaxis': 'y1'}
            humidity_trace2 = {'x': timestamps, 'y': humidity, 'type': 'scatter', 'mode': 'lines', 'name': 'Humidity', 'line': {'color': '#4ecdc4'}, 'yaxis': 'y2'}
            layout = get_plotly_dark_layout('Temperature & Humidity Over Time', 'Time', 'Temperature (C)')
            layout['yaxis2'] = {'title': 'Humidity (%)', 'titlefont': {'color': '#4ecdc4'}, 'tickfont': {'color': '#4ecdc4'}, 'overlaying': 'y', 'side': 'right', 'gridcolor': 'rgba(255,255,255,0.05)'}
            layout['yaxis']['titlefont'] = {'color': '#ff6b6b'}
            layout['yaxis']['tickfont'] = {'color': '#ff6b6b'}
            charts.append({'title': 'Temperature & Humidity Over Time', 'data': [temp_trace2, humidity_trace2], 'layout': layout, 'type': 'multi'})
        
        # 6. Rainfall Pattern
        if any(rainfall):
            rainfall_trace = {'x': timestamps, 'y': rainfall, 'type': 'bar', 'name': 'Rainfall', 'marker': {'color': '#6bcf7f'}}
            charts.append({'title': 'Rainfall Pattern', 'data': [rainfall_trace], 'layout': get_plotly_dark_layout('Rainfall Pattern', 'Time', 'Rainfall (mm)', hovermode='x'), 'type': 'rainfall'})
        
        return jsonify({'statistics': statistics, 'charts': charts})
    except Exception as e:
        print(f"Error in advanced weather data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'charts': [], 'statistics': {}})

@app.route('/api/weather-dashboard-data')
@login_required
def api_weather_dashboard_data():
    """Get weather dashboard data."""
    try:
        connection = create_connection()
        if not connection:
            return jsonify({
                'weather_cards': [],
                'summary': {},
                'charts': {},
                'alerts': []
            })
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                wd.location_name AS location,
                COALESCE(wl.country, '') AS country,
                wd.temperature,
                wd.weather_main AS weather,
                wd.weather_description AS description,
                wd.feels_like,
                wd.humidity,
                wd.wind_speed,
                wd.pressure,
                wd.cloudiness,
                wd.timestamp AS last_updated
            FROM weather_data wd
            INNER JOIN (
                SELECT location_name, MAX(timestamp) AS max_ts
                FROM weather_data
                GROUP BY location_name
            ) latest
                ON latest.location_name = wd.location_name
               AND latest.max_ts = wd.timestamp
            LEFT JOIN weather_locations wl
                ON wl.location_name = wd.location_name
            ORDER BY wd.location_name ASC
        """)
        weather_cards = cursor.fetchall()

        cursor.execute("""
            SELECT location_name, timestamp, temperature, humidity, wind_speed, weather_main
            FROM weather_data
            ORDER BY timestamp ASC
            LIMIT 1500
        """)
        history_rows = cursor.fetchall()

        timestamp = weather_cards[0].get('last_updated') if weather_cards else None

        # Summary
        total_locations = len(weather_cards)
        avg_temperature = round(sum(float(r.get('temperature') or 0) for r in weather_cards) / total_locations, 1) if total_locations else 0
        avg_humidity = round(sum(float(r.get('humidity') or 0) for r in weather_cards) / total_locations, 1) if total_locations else 0
        avg_wind_speed = round(sum(float(r.get('wind_speed') or 0) for r in weather_cards) / total_locations, 1) if total_locations else 0

        # Build chart data
        by_location = {}
        weather_counts = {}
        for row in history_rows:
            loc = row.get('location_name') or 'Unknown'
            by_location.setdefault(loc, {'x': [], 'temp': [], 'humidity': [], 'wind': []})
            by_location[loc]['x'].append(str(row.get('timestamp')))
            by_location[loc]['temp'].append(float(row.get('temperature') or 0))
            by_location[loc]['humidity'].append(float(row.get('humidity') or 0))
            by_location[loc]['wind'].append(float(row.get('wind_speed') or 0))

            weather_name = row.get('weather_main') or 'Unknown'
            weather_counts[weather_name] = weather_counts.get(weather_name, 0) + 1

        temp_traces = []
        humidity_traces = []
        for loc, series in by_location.items():
            temp_traces.append({
                'x': series['x'],
                'y': series['temp'],
                'type': 'scatter',
                'mode': 'lines',
                'name': loc
            })
            humidity_traces.append({
                'x': series['x'],
                'y': series['humidity'],
                'type': 'scatter',
                'mode': 'lines',
                'name': loc
            })

        wind_chart = {
            'data': [{
                'x': [r.get('location') for r in weather_cards],
                'y': [float(r.get('wind_speed') or 0) for r in weather_cards],
                'type': 'bar',
                'marker': {'color': '#7c3aed'}
            }],
            'layout': {
                'title': 'Wind Speed by Location',
                'margin': {'l': 50, 'r': 20, 't': 40, 'b': 60},
                'plot_bgcolor': '#f8fafc',
                'paper_bgcolor': 'transparent',
                'xaxis': {'title': 'Location'},
                'yaxis': {'title': 'Wind Speed (m/s)'}
            }
        }

        weather_dist_chart = {
            'data': [{
                'labels': list(weather_counts.keys()),
                'values': list(weather_counts.values()),
                'type': 'pie',
                'textinfo': 'label+percent'
            }],
            'layout': {
                'title': 'Weather Condition Distribution',
                'margin': {'l': 20, 'r': 20, 't': 40, 'b': 20},
                'paper_bgcolor': 'transparent'
            }
        }
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'weather_cards': weather_cards,
            'summary': {
                'total_locations': total_locations,
                'avg_temperature': avg_temperature,
                'avg_humidity': avg_humidity,
                'avg_wind_speed': avg_wind_speed
            },
            'charts': {
                'temp_comparison': {
                    'data': temp_traces,
                    'layout': {
                        'title': 'Temperature Comparison',
                        'hovermode': 'x unified',
                        'margin': {'l': 50, 'r': 20, 't': 40, 'b': 40},
                        'plot_bgcolor': '#f8fafc',
                        'paper_bgcolor': 'transparent',
                        'xaxis': {'title': 'Time'},
                        'yaxis': {'title': 'Temperature (C)'}
                    }
                },
                'humidity': {
                    'data': humidity_traces,
                    'layout': {
                        'title': 'Humidity Trend',
                        'hovermode': 'x unified',
                        'margin': {'l': 50, 'r': 20, 't': 40, 'b': 40},
                        'plot_bgcolor': '#f8fafc',
                        'paper_bgcolor': 'transparent',
                        'xaxis': {'title': 'Time'},
                        'yaxis': {'title': 'Humidity (%)'}
                    }
                },
                'wind': wind_chart,
                'weather_dist': weather_dist_chart
            },
            'alerts': [],
            'last_updated': timestamp
        })
    except Exception as e:
        print(f"Weather dashboard error: {e}")
        return jsonify({
            'weather_cards': [],
            'summary': {},
            'charts': {},
            'alerts': []
        })

@app.route('/api/sync-weather', methods=['GET'])
@login_required
def api_sync_weather():
    """Read-only API: return the latest weather snapshot (does NOT trigger fetch)."""
    try:
        connection = create_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT *
            FROM weather_latest
            ORDER BY last_updated DESC, location_name ASC
        """)
        rows = cursor.fetchall()
        
        # Get the most recent timestamp
        timestamp = None
        if rows:
            timestamp = rows[0].get('last_updated')
        
        cursor.close()
        connection.close()
        
        return jsonify({'success': True, 'data': rows, 'last_updated': timestamp})
    except Exception as e:
        print(f"Weather read error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/social-trends-dashboard-data')
@login_required
def api_social_trends_dashboard_data():
    """Get social trends dashboard data with latest timestamp."""
    try:
        connection = create_connection()
        if not connection:
            return jsonify({
                'trends': [],
                'statistics': {},
                'last_updated': None
            })
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT source_platform, trend_name, 'topic' AS trend_type, rank_position, volume,
                   engagement_count, sentiment, NULL AS description, trend_url, data_collected_at
            FROM social_latest
            ORDER BY source_platform ASC, rank_position ASC, engagement_count DESC
            LIMIT 500
        """)
        trends = cursor.fetchall()
        
        # Get the most recent timestamp
        timestamp = None
        if trends:
            timestamp = trends[0].get('data_collected_at')
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'trends': trends,
            'statistics': {'total_trends': len(trends)},
            'last_updated': timestamp
        })
    except Exception as e:
        print(f"Social trends dashboard error: {e}")
        return jsonify({
            'trends': [],
            'statistics': {},
            'last_updated': None
        })

# ==================== WEATHER LOCATIONS MANAGEMENT ====================


@app.route('/manage-locations')
@login_required
def manage_locations():
    """Display location management page."""
    return render_template("locations_management.html")

@app.route('/api/weather-locations', methods=['GET', 'POST'])
@login_required
def api_weather_locations():
    """Get or add weather locations."""
    if request.method == 'GET':
        locations = WeatherLocationsManager.get_all_locations(active_only=False)
        return jsonify({
            'success': True,
            'all_locations': locations
        })
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            result = WeatherLocationsManager.add_location(
                location_name=data.get('location_name'),
                country=data.get('country'),
                latitude=float(data.get('latitude')),
                longitude=float(data.get('longitude')),
                notes=data.get('notes')
            )
            
            if result:
                return jsonify({
                    'success': True,
                    'message': 'Location added successfully!'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to add location (duplicate name?)'
                })
        except Exception as e:
            print(f"Error adding location: {e}")
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400

@app.route('/api/weather-locations/<int:location_id>', methods=['DELETE'])
@login_required
def api_delete_location(location_id):
    """Delete a location."""
    try:
        result = WeatherLocationsManager.delete_location(location_id)
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Location deleted successfully!'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to delete location'
            })
    except Exception as e:
        print(f"Error deleting location: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@app.route('/api/weather-locations/<int:location_id>/toggle', methods=['POST'])
@login_required
def api_toggle_location(location_id):
    """Toggle location active status."""
    try:
        location = WeatherLocationsManager.get_location(location_id)
        
        if not location:
            return jsonify({
                'success': False,
                'message': 'Location not found'
            }), 404
        
        new_status = not location['is_active']
        result = WeatherLocationsManager.update_location(location_id, is_active=new_status)
        
        if result:
            status_text = 'activated' if new_status else 'deactivated'
            return jsonify({
                'success': True,
                'message': f'Location {status_text} successfully!'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to update location'
            })
    except Exception as e:
        print(f"Error toggling location: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

# ==================== SOCIAL MEDIA TRENDS DASHBOARDS ====================

@app.route('/social-trends-dashboard')
@login_required
def social_trends_dashboard():
    """Display social media trends dashboard with platform filter."""
    try:
        from database.social_media_models import get_all_trends
        generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        trends = get_all_trends(limit=500)

        trends_list = []
        if trends:
            for trend in trends:
                trends_list.append({
                    'platform': trend[0] if len(trend) > 0 else 'Unknown',
                    'name': trend[1] if len(trend) > 1 else '',
                    'type': trend[2] if len(trend) > 2 else 'topic',
                    'rank': trend[3] if len(trend) > 3 else 0,
                    'volume': trend[4] if len(trend) > 4 else 0,
                    'engagement': trend[5] if len(trend) > 5 else 0,
                    'sentiment': trend[6] if len(trend) > 6 else 'neutral',
                    'url': trend[8] if len(trend) > 8 else None,
                })

        total_trends = len(trends_list)
        platforms = sorted(list(set([t['platform'] for t in trends_list])))

        for trend in trends_list:
            raw_engagement = int(trend.get('engagement') or 0)
            raw_volume = int(trend.get('volume') or 0)
            rank_value = int(trend.get('rank') or 0)
            rank_fallback = max(total_trends - rank_value + 1, 1) if rank_value > 0 else total_trends
            trend['display_engagement'] = raw_engagement if raw_engagement > 0 else (
                raw_volume if raw_volume > 0 else rank_fallback
            )

        avg_engagement = (
            sum([t['display_engagement'] for t in trends_list]) / len(trends_list)
            if trends_list else 0
        )

        trends_json = []
        if trends_list:
            ordered_trends = sorted(
                trends_list,
                key=lambda x: (
                    -(x.get('display_engagement') or 0),
                    x.get('rank') if x.get('rank') is not None else 999999,
                    str(x.get('platform') or '').lower(),
                ),
            )
            for idx, trend in enumerate(ordered_trends[:300], 1):
                platform = trend['platform'].lower().replace(' ', '-')
                sentiment_class = f"badge-{trend['sentiment']}"
                platform_class = f"badge-{platform}"
                trends_json.append({
                    'rank': idx,
                    'name': trend['name'][:60],
                    'platform': trend['platform'],
                    'platform_class': platform_class,
                    'type': trend['type'],
                    'engagement': int(trend.get('display_engagement', 0)),
                    'sentiment': trend['sentiment'],
                    'sentiment_class': sentiment_class,
                    'url': trend.get('url'),
                })

        return render_template(
            "social_trends_dashboard.html",
            generated_at=generated_at,
            total_trends=total_trends,
            platforms=platforms,
            platform_count=len(platforms),
            avg_engagement=int(avg_engagement),
            trends_json=trends_json,
        )
    except Exception as e:
        print(f"Error loading social trends: {e}")
        import traceback
        traceback.print_exc()
        return render_template("dashboard_error.html", title="Social Trends Error", message=str(e))

@app.route('/advanced-social-trends-dashboard')
@login_required
def advanced_social_trends_dashboard():
    """Display advanced social trends analytics dashboard."""
    try:
        from database.social_media_models import get_all_trends
        generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Fetch trends from database
        trends = get_all_trends(limit=500)
        
        # Convert to list of dicts
        trends_list = []
        if trends:
            for trend in trends:
                trends_list.append({
                    'platform': trend[0] if len(trend) > 0 else 'Unknown',
                    'name': trend[1] if len(trend) > 1 else '',
                    'type': trend[2] if len(trend) > 2 else 'topic',
                    'rank': trend[3] if len(trend) > 3 else 0,
                    'engagement': trend[5] if len(trend) > 5 else 0,
                    'sentiment': trend[6] if len(trend) > 6 else 'neutral'
                })
        
        emerging = len([t for t in trends_list if t['engagement'] > 5000])
        declining = len([t for t in trends_list if t['engagement'] < 2000])
        platform_counts = {}
        sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
        
        for t in trends_list:
            p = t['platform']
            platform_counts[p] = platform_counts.get(p, 0) + 1
            s = t['sentiment']
            if s in sentiment_counts:
                sentiment_counts[s] += 1
        
        top_platform = max(platform_counts, key=platform_counts.get) if platform_counts else 'N/A'
        platform_counts_sorted = sorted(platform_counts.items(), key=lambda x: x[1], reverse=True)

        return render_template(
            "advanced_social_trends_dashboard.html",
            generated_at=generated_at,
            emerging=emerging,
            declining=declining,
            platform_count=len(platform_counts),
            top_platform=top_platform,
            sentiment_counts=sentiment_counts,
            platform_counts=platform_counts_sorted,
        )
    except Exception as e:
        print(f"Error loading advanced trends: {e}")
        import traceback
        traceback.print_exc()
        return render_template("dashboard_error.html", title="Advanced Trends Error", message=str(e))


# API endpoints removed - dashboards now render data server-side for better reliability

# ==================== REDIRECT ====================

@app.route('/api/force-sync', methods=['POST'])
@login_required
def api_force_sync():
    """Manually trigger data sync for crypto, social media, and weather (requires login)."""
    try:
        print("Starting manual force sync via UI...")
        
        # Ensure database is initialized with default assets/cities if empty
        bootstrap_all()
        
        from scheduler.job import scrape_and_store, sync_social_media_trends
        
        # Run sync tasks
        scrape_and_store()
        sync_social_media_trends()
        sync_weather_job()
        
        return jsonify({"success": True, "message": "Data synchronization complete!"})
    except Exception as e:
        print(f"Error during manual sync: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/cron/sync')
def cron_sync():
    """Trigger data sync for crypto, social media, and weather."""
    # Check for Vercel Cron secret (recommended for security)
    auth_header = request.headers.get('Authorization')
    cron_secret = os.getenv('CRON_SECRET')
    
    if cron_secret and auth_header != f"Bearer {cron_secret}":
        print("Unauthorized cron attempt")
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        print("Starting scheduled sync via API...")
        # Import inside the function to avoid circular imports
        from scheduler.job import scrape_and_store, sync_social_media_trends
        
        # Run sync tasks
        scrape_and_store()
        sync_social_media_trends()
        sync_weather_job()
        
        print("API sync complete.")
        return jsonify({"status": "success", "message": "All data synchronized"})
    except Exception as e:
        print(f"Error during API sync: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    """Redirect to login if not logged in."""
    token = request.cookies.get('auth_token')
    if token and AuthManager.verify_session(token):
        return redirect(url_for('menu'))
    return redirect(url_for('login'))

def bootstrap_all():
    """Initialize all database tables and settings."""
    try:
        print("Initializing database tables for serverless environment...")
        
        # Predefined cities
        PredefinedCitiesManager.create_table()
        PredefinedCitiesManager.initialize_default_cities()
        
        # Preferred assets
        from database.preferred_assets import PreferredAssetsManager
        PreferredAssetsManager.create_table()
        PreferredAssetsManager.initialize_default_assets()
        
        # Weather Locations
        from database.weather_locations import WeatherLocationsManager
        WeatherLocationsManager.create_table()
        WeatherLocationsManager.initialize_default_locations()
        
        # Core crypto_assets table (THE MAIN TABLE - must be created first)
        from database.connection import create_table, create_weather_table, create_weather_locations_table, create_crypto_latest_table, create_weather_latest_table, create_social_latest_table, create_signal_fusion_index_table
        create_table()  # crypto_assets table
        create_weather_table()
        create_weather_locations_table()
        create_crypto_latest_table()
        create_weather_latest_table()
        create_social_latest_table()
        create_signal_fusion_index_table()
        
        # Alert tables
        from database.alert_models import create_alerts_table, create_weather_alerts_table, create_social_trend_alerts_table
        create_alerts_table()
        create_weather_alerts_table()
        create_social_trend_alerts_table()
        
        # Access control (MUST BE FIRST - others depend on app_users)
        from database.access_control import create_access_control_tables, seed_default_access_config
        create_access_control_tables()
        seed_default_access_config()

        # UI Settings
        from database.ui_settings import create_ui_settings_table
        create_ui_settings_table()
        
        # User preferences
        from database.user_preferences import create_user_preferences_table, initialize_default_users
        create_user_preferences_table()
        initialize_default_users()
        
        # Initialize crypto assets and populate cache
        init_crypto_assets()
        load_initial_data_to_cache()

        print("✓ Database initialization complete.")
    except Exception as e:
        import traceback
        print(f"Error during bootstrap: {e}")
        traceback.print_exc()

# Call bootstrap when the app is initialized in Vercel
if os.environ.get('VERCEL'):
    bootstrap_all()

if __name__ == '__main__':
    print("Starting RPA Framework...")
    bootstrap_all()
    
    print("\n" + "="*60)
    print(" RPA Framework is running!")
    print("="*60)
    print("Dashboard URL: http://localhost:5000")
    print("Default Login: admin / admin")
    print("="*60 + "\n")

    # Start Flask app
    port = int(os.environ.get("FLASK_RUN_PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
