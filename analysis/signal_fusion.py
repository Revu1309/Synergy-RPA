"""Signal Fusion Index computation using existing stored snapshots/history."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from database.connection import create_connection
from database.models import insert_signal_fusion_index


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _scale_0_100(value01: float) -> float:
    return round(_clamp01(value01) * 100.0, 2)


def _safe_div(num: float, den: float) -> float:
    if den == 0:
        return 0.0
    return num / den


def _compute_crypto_score(cursor) -> Tuple[float, bool]:
    # Last 24h per-symbol prices/volumes from historical table.
    cursor.execute(
        """
        SELECT symbol, price_usd, volume_24h, timestamp
        FROM crypto_assets
        WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
          AND price_usd IS NOT NULL
          AND volume_24h IS NOT NULL
        """
    )
    rows = cursor.fetchall()
    if not rows:
        return 0.0, False

    # Volatility proxy: mean of per-symbol (std/mean), clipped to a 15% band.
    by_symbol: Dict[str, List[Tuple[float, float, datetime]]] = {}
    for symbol, price, volume, ts in rows:
        by_symbol.setdefault(symbol, []).append((float(price), float(volume), ts))

    vol_ratios: List[float] = []
    recent_volumes: List[float] = []
    prev_volumes: List[float] = []

    now = datetime.utcnow()
    recent_cutoff = now - timedelta(hours=3)
    prev_cutoff = now - timedelta(hours=6)

    for points in by_symbol.values():
        prices = [p for p, _, _ in points]
        if len(prices) >= 2:
            mean_price = sum(prices) / len(prices)
            variance = sum((p - mean_price) ** 2 for p in prices) / (len(prices) - 1)
            stddev = variance ** 0.5
            vol_ratios.append(_safe_div(stddev, mean_price))

        for _, vol, ts in points:
            if ts and ts >= recent_cutoff:
                recent_volumes.append(vol)
            elif ts and prev_cutoff <= ts < recent_cutoff:
                prev_volumes.append(vol)

    avg_vol_ratio = sum(vol_ratios) / len(vol_ratios) if vol_ratios else 0.0
    vol_score = _clamp01(avg_vol_ratio / 0.15)

    recent_avg = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 0.0
    prev_avg = sum(prev_volumes) / len(prev_volumes) if prev_volumes else 0.0
    volume_delta = abs(_safe_div(recent_avg - prev_avg, prev_avg))
    volume_score = _clamp01(volume_delta / 1.0)

    combined = (0.6 * vol_score) + (0.4 * volume_score)
    return _scale_0_100(combined), True


def _compute_social_score(cursor) -> Tuple[float, bool]:
    # Trend count change from historical social_trends.
    cursor.execute(
        """
        SELECT
            SUM(CASE WHEN data_collected_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 ELSE 0 END) AS recent_count,
            SUM(CASE WHEN data_collected_at >= DATE_SUB(NOW(), INTERVAL 2 HOUR)
                      AND data_collected_at < DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 ELSE 0 END) AS prev_count
        FROM social_trends
        WHERE data_collected_at >= DATE_SUB(NOW(), INTERVAL 2 HOUR)
        """
    )
    recent_count, prev_count = cursor.fetchone()
    recent_count = int(recent_count or 0)
    prev_count = int(prev_count or 0)

    # Cross-platform presence from latest snapshot.
    cursor.execute("SELECT COUNT(DISTINCT source_platform) FROM social_latest")
    platform_count = int((cursor.fetchone() or [0])[0] or 0)

    if recent_count == 0 and prev_count == 0 and platform_count == 0:
        return 0.0, False

    count_change = abs(_safe_div(recent_count - prev_count, prev_count if prev_count > 0 else max(recent_count, 1)))
    count_change_score = _clamp01(count_change / 1.0)

    # Normalize against 8 expected active platforms.
    platform_presence_score = _clamp01(platform_count / 8.0)

    combined = (0.6 * count_change_score) + (0.4 * platform_presence_score)
    return _scale_0_100(combined), True


def _compute_weather_score(cursor) -> Tuple[float, bool]:
    cursor.execute(
        """
        SELECT temperature, wind_speed, rainfall, snow, pressure, last_updated
        FROM weather_latest
        """
    )
    rows = cursor.fetchall()
    if not rows:
        return 0.0, False

    risk_values: List[float] = []
    for temp, wind, rain, snow, pressure, _ in rows:
        risk = 0.0

        if temp is not None:
            t = float(temp)
            if t >= 35 or t <= 0:
                risk += 0.35
            elif t >= 30 or t <= 5:
                risk += 0.15

        if wind is not None:
            w = float(wind)
            if w >= 40:
                risk += 0.30
            elif w >= 25:
                risk += 0.15

        if rain is not None:
            r = float(rain)
            if r >= 20:
                risk += 0.20
            elif r >= 8:
                risk += 0.10

        if snow is not None:
            s = float(snow)
            if s >= 5:
                risk += 0.20
            elif s >= 1:
                risk += 0.10

        if pressure is not None:
            p = float(pressure)
            if p < 980 or p > 1030:
                risk += 0.15
            elif p < 990 or p > 1025:
                risk += 0.08

        risk_values.append(_clamp01(risk))

    risk_avg = sum(risk_values) / len(risk_values) if risk_values else 0.0
    return _scale_0_100(risk_avg), True


def compute_signal_fusion_scores() -> Dict[str, object]:
    """Compute component and fusion scores from persisted project data."""
    connection = create_connection()
    if not connection:
        return {
            "crypto_score": 0.0,
            "social_score": 0.0,
            "weather_score": 0.0,
            "fusion_score": 0.0,
            "confidence_level": "Low",
        }

    cursor = connection.cursor()
    try:
        crypto_score, has_crypto = _compute_crypto_score(cursor)
        social_score, has_social = _compute_social_score(cursor)
        weather_score, has_weather = _compute_weather_score(cursor)

        fusion = round((0.4 * crypto_score) + (0.4 * social_score) + (0.2 * weather_score), 2)

        available = sum([1 if has_crypto else 0, 1 if has_social else 0, 1 if has_weather else 0])
        if available >= 3:
            confidence = "High"
        elif available == 2:
            confidence = "Medium"
        else:
            confidence = "Low"

        return {
            "crypto_score": crypto_score,
            "social_score": social_score,
            "weather_score": weather_score,
            "fusion_score": fusion,
            "confidence_level": confidence,
        }
    finally:
        cursor.close()
        connection.close()


def compute_and_store_signal_fusion_index() -> Dict[str, object]:
    """Compute and persist one Signal Fusion Index snapshot row."""
    scores = compute_signal_fusion_scores()
    insert_signal_fusion_index(
        crypto_score=scores["crypto_score"],
        social_score=scores["social_score"],
        weather_score=scores["weather_score"],
        fusion_score=scores["fusion_score"],
        confidence_level=scores["confidence_level"],
    )
    return scores

