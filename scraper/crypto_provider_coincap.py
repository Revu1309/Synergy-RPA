"""
crypto_provider_coincap.py

Drop-in replacement for CoinGecko-based crypto fetching.
Uses CoinCap public API (no API key, high free limits).

Expected usage:
    from crypto_provider_coincap import fetch_crypto_prices

Returns:
    A list of dicts with fields compatible with existing DB insert logic.
"""

import requests
from datetime import datetime, timezone

COINCAP_ASSETS_URL = "https://api.coincap.io/v2/assets"

# Map CoinCap asset IDs to your symbols if needed
# Example: {"bitcoin": "BTC", "ethereum": "ETH"}
ASSET_ID_TO_SYMBOL = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "tether": "USDT",
    "binance-coin": "BNB",
    "solana": "SOL",
    "usd-coin": "USDC",
}


def fetch_crypto_prices():
    """
    Fetch crypto prices from CoinCap in a single bulk call.
    Returns a list of dicts ready for DB insertion.
    """
    response = requests.get(COINCAP_ASSETS_URL, timeout=15)
    response.raise_for_status()

    payload = response.json()
    assets = payload.get("data", [])

    now = datetime.now(timezone.utc)

    records = []

    for asset in assets:
        asset_id = asset.get("id")
        if asset_id not in ASSET_ID_TO_SYMBOL:
            continue

        try:
            records.append({
                "symbol": ASSET_ID_TO_SYMBOL[asset_id],
                "price_usd": float(asset.get("priceUsd")),
                "market_cap": float(asset.get("marketCapUsd")),
                "volume_24h": float(asset.get("volumeUsd24Hr")),
                "timestamp": now,
                "source": "coincap",
            })
        except (TypeError, ValueError):
            # Skip malformed rows
            continue

    return records
