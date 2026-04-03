"""
scraper/coinmarketcap.py

Dynamic crypto scraper (Binance-based).
- Reads symbols + names from preferred_assets
- Calculates market_cap = price_usd * circulating_supply (if available)
- Uses Binance public API (DNS-safe)
- Loads .env internally
"""

import requests
from datetime import datetime, timezone
import mysql.connector
import os

# Load .env locally
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

BINANCE_TICKER_URL = "https://api.binance.com/api/v3/ticker/24hr"
BINANCE_SUPPLY_URL = "https://api.binance.com/api/v3/exchangeInfo"


def _get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DATABASE_HOST"),
        user=os.getenv("DATABASE_USER"),
        password=os.getenv("DATABASE_PASSWORD"),
        database=os.getenv("DATABASE_NAME"),
        autocommit=True
    )


def _get_preferred_assets():
    conn = _get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT symbol, name FROM preferred_assets")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_crypto_data():
    assets = _get_preferred_assets()
    if not assets:
        return []

    symbol_to_name = {a["symbol"].upper(): a["name"] for a in assets}
    wanted_pairs = {f"{sym}USDT": sym for sym in symbol_to_name}

    prices = requests.get(BINANCE_TICKER_URL, timeout=15).json()
    now = datetime.now(timezone.utc)

    results = []

    for item in prices:
        pair = item.get("symbol")
        if pair not in wanted_pairs:
            continue

        sym = wanted_pairs[pair]
        price = float(item.get("lastPrice"))
        volume = float(item.get("quoteVolume"))

        # Binance does not provide circulating supply → market cap cannot be calculated reliably
        market_cap = None

        results.append({
            "symbol": sym,
            "name": symbol_to_name.get(sym),
            "price_usd": price,
            "volume_24h": volume,
            "market_cap": market_cap,
            "timestamp": now,
            "source": "binance",
        })

    return results
