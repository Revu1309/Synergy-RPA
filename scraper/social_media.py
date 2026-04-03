"""
social_media.py

DB-driven social media sync.
- Reads sources from social_media_sources table
- Routes by data_collection_method (api | rss | scraper | hybrid)
- Respects update_frequency_minutes
- Updates last_sync after successful sync
"""

import requests
import mysql.connector
import os
import re
import html
from datetime import datetime, timedelta, timezone
from database.social_media_models import insert_social_trend, insert_trend_history
from database.models import upsert_social_latest

# Load .env locally
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

PLATFORM_LABELS = {
    "reddit": "Reddit",
    "hackernews": "Hacker News",
    "hackernews_algolia": "Hacker News",
    "stackoverflow": "Stack Overflow",
    "devto": "Dev.to",
    "producthunt": "Product Hunt",
    "youtube": "YouTube",
    "lobsters": "Lobsters",
    "twitter": "Twitter",
}


def _canonical_platform_name(platform_name, platform_display_name=None):
    raw = (platform_display_name or platform_name or "").strip()
    key = raw.lower().replace(" ", "").replace("-", "").replace("_", "")
    normalized = {
        "reddit": "Reddit",
        "hackernews": "Hacker News",
        "hackernewsalgolia": "Hacker News",
        "stackoverflow": "Stack Overflow",
        "devto": "Dev.to",
        "producthunt": "Product Hunt",
        "youtube": "YouTube",
        "lobsters": "Lobsters",
        "twitter": "Twitter",
    }
    return normalized.get(key) or PLATFORM_LABELS.get((platform_name or "").lower()) or raw or "Unknown"


def _clean_text(value):
    if value is None:
        return ""
    text = html.unescape(str(value))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _safe_int(value, default=0):
    if value is None:
        return default
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return int(value)
    text = re.sub(r"[^\d\-]", "", str(value))
    if not text:
        return default
    try:
        return int(text)
    except Exception:
        return default


def _is_bad_trend_name(name):
    if not name:
        return True
    lowered = name.lower()
    if lowered in {"[deleted]", "[removed]", "none", "null"}:
        return True
    if re.fullmatch(r"t3_[a-z0-9]+", lowered):
        return True
    if re.fullmatch(r"\d{5,}", name):
        return True
    return False


def _extract_trend_url(payload, platform_name):
    candidates = [
        payload.get("trend_url"),
        payload.get("url"),
        payload.get("link"),
        payload.get("permalink"),
        payload.get("short_id_url"),
        payload.get("canonical_url"),
        payload.get("html_url"),
        payload.get("story_url"),
    ]
    trend_url = None
    for candidate in candidates:
        if candidate:
            trend_url = str(candidate).strip()
            break

    if trend_url and trend_url.startswith("/"):
        if platform_name == "reddit":
            trend_url = f"https://www.reddit.com{trend_url}"
        elif "hackernews" in platform_name:
            trend_url = f"https://news.ycombinator.com{trend_url}"

    if (not trend_url) and "hackernews" in platform_name:
        story_id = payload.get("id") or payload.get("objectID")
        if story_id:
            trend_url = f"https://news.ycombinator.com/item?id={story_id}"

    if trend_url and trend_url.startswith("http"):
        return trend_url[:1000]
    return None


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DATABASE_HOST"),
        user=os.getenv("DATABASE_USER"),
        password=os.getenv("DATABASE_PASSWORD"),
        database=os.getenv("DATABASE_NAME"),
        autocommit=True
    )


def get_active_sources():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT *
        FROM social_media_sources
        WHERE is_active = 1
          AND scraper_enabled = 1
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def should_run(source):
    last_sync = source.get("last_sync")
    if not last_sync:
        return True
    interval = source.get("update_frequency_minutes") or 60
    next_run = last_sync + timedelta(minutes=int(interval))

    # MySQL connector returns naive datetimes by default. Compare like-with-like.
    if getattr(next_run, "tzinfo", None) is None:
        return datetime.utcnow() >= next_run
    return datetime.now(timezone.utc) >= next_run


def fetch_api(url, max_items):
    params = None
    normalized_url = url

    # Resolve common template placeholders from source config.
    if "{subreddit}" in normalized_url:
        normalized_url = normalized_url.replace("{subreddit}", "python")

    # StackExchange API requires a `site` parameter.
    if "api.stackexchange.com" in normalized_url and "site=" not in normalized_url:
        params = {"site": "stackoverflow", "order": "desc", "sort": "votes", "pagesize": max_items}

    r = requests.get(
        normalized_url,
        params=params,
        timeout=15,
        headers={"User-Agent": "RPA-Trend-Sync"},
    )
    r.raise_for_status()
    data = r.json()

    # Hacker News topstories returns only IDs; fetch story documents for usable titles/links.
    if "hacker-news.firebaseio.com/v0/topstories" in normalized_url and isinstance(data, list):
        stories = []
        for story_id in data[:max_items]:
            try:
                item_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                item_resp = requests.get(item_url, timeout=10, headers={"User-Agent": "RPA-Trend-Sync"})
                item_resp.raise_for_status()
                item_data = item_resp.json()
                if isinstance(item_data, dict):
                    stories.append(item_data)
            except Exception:
                continue
        return stories

    if isinstance(data, list):
        return data[:max_items]

    if isinstance(data, dict):
        nested_data = data.get("data")
        if isinstance(nested_data, dict):
            children = nested_data.get("children")
            if isinstance(children, list):
                return children[:max_items]
        for key in ("items", "hits", "data", "results", "stories", "children"):
            value = data.get(key)
            if isinstance(value, list):
                return value[:max_items]
        return [data]

    return []


def fetch_rss(url, max_items):
    if "{channel_id}" in url:
        # Public Google Developers channel fallback for template URLs.
        url = url.replace("{channel_id}", "UC_x5XG1OV2P6uZZ5FSM9Ttw")
    try:
        import feedparser
        feed = feedparser.parse(url)
        return feed.entries[:max_items]
    except Exception:
        # Fallback when feedparser is unavailable.
        import xml.etree.ElementTree as ET

        resp = requests.get(url, timeout=15, headers={"User-Agent": "RPA-Trend-Sync"})
        resp.raise_for_status()
        root = ET.fromstring(resp.content)

        entries = []
        # RSS
        for item in root.findall(".//item"):
            entries.append(
                {
                    "title": item.findtext("title"),
                    "link": item.findtext("link"),
                    "description": item.findtext("description"),
                }
            )
            if len(entries) >= max_items:
                return entries

        # Atom
        ns_link = "{http://www.w3.org/2005/Atom}link"
        ns_title = "{http://www.w3.org/2005/Atom}title"
        ns_summary = "{http://www.w3.org/2005/Atom}summary"
        for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry"):
            link_node = entry.find(ns_link)
            entries.append(
                {
                    "title": entry.findtext(ns_title),
                    "link": (link_node.attrib.get("href") if link_node is not None else None),
                    "description": entry.findtext(ns_summary),
                }
            )
            if len(entries) >= max_items:
                return entries
        return entries


def _normalize_trends(items, source, max_items):
    """Normalize API/RSS payloads to a common trend shape."""
    normalized = []
    seq = items if isinstance(items, list) else [items]
    platform_key = str(source.get("platform_name") or "").lower()
    platform_name = _canonical_platform_name(
        source.get("platform_name"),
        source.get("platform_display_name"),
    )

    for idx, item in enumerate(seq[:max_items], start=1):
        if hasattr(item, "get"):
            payload = item.get("data") if isinstance(item.get("data"), dict) else item
            trend_name = (
                payload.get("trend_name")
                or payload.get("title")
                or payload.get("name")
                or payload.get("keyword")
                or payload.get("tag")
            )
            trend_type = payload.get("trend_type") or "keyword"
            rank = payload.get("rank_position") or payload.get("rank") or idx
            volume = (
                payload.get("volume")
                or payload.get("mentions")
                or payload.get("ups")
                or payload.get("view_count")
                or 0
            )
            engagement = (
                payload.get("engagement_count")
                or payload.get("engagement")
                or payload.get("interactions")
                or payload.get("num_comments")
                or payload.get("score")
                or payload.get("points")
                or 0
            )
            sentiment = payload.get("sentiment") or "neutral"
            description = payload.get("description") or payload.get("summary") or payload.get("selftext")
            trend_url = _extract_trend_url(payload, platform_key)
        else:
            trend_name = str(item)
            trend_type = "keyword"
            rank = idx
            volume = 0
            engagement = 0
            sentiment = "neutral"
            description = None
            trend_url = None

        trend_name = _clean_text(trend_name)
        description = _clean_text(description) if description else None
        trend_type = _clean_text(trend_type) or "keyword"
        sentiment = (_clean_text(sentiment) or "neutral").lower()

        if _is_bad_trend_name(trend_name):
            continue

        normalized.append({
            "trend_name": trend_name[:255],
            "trend_type": trend_type[:20],
            "source_platform": platform_name,
            "rank_position": _safe_int(rank, idx),
            "volume": _safe_int(volume, 0),
            "engagement_count": _safe_int(engagement, 0),
            "sentiment": sentiment[:20],
            "description": (description[:1000] if description else None),
            "trend_url": trend_url,
        })

    return normalized


def sync_social_media():
    sources = get_active_sources()
    # Use naive UTC for MySQL TIMESTAMP writes (mysql-connector expects naive dt).
    now = datetime.utcnow()
    force_all = os.getenv("SOCIAL_SYNC_FORCE_ALL", "1").strip().lower() in ("1", "true", "yes", "on")

    for src in sources:
        if not force_all:
            try:
                should_fetch = should_run(src)
            except Exception as e:
                print(f"[SOCIAL] {src.get('platform_name', 'unknown')} schedule check failed: {e}")
                continue

            if not should_fetch:
                continue

        try:
            method = src["data_collection_method"]
            endpoint = src["api_endpoint"]
            max_items = int(src.get("max_trends") or 20)

            if not endpoint:
                print(f"[SOCIAL] {src['platform_name']} skipped: missing api_endpoint")
                continue

            if method == "api":
                data = fetch_api(endpoint, max_items)
            elif method == "rss":
                data = fetch_rss(endpoint, max_items)

            else:
                # scraper / hybrid not implemented yet
                continue

            normalized = _normalize_trends(data, src, max_items)

            for t in normalized:
                insert_social_trend(
                    trend_name=t["trend_name"],
                    trend_type=t["trend_type"],
                    source_platform=t["source_platform"],
                    rank_position=t["rank_position"],
                    volume=t["volume"],
                    engagement_count=t["engagement_count"],
                    sentiment=t["sentiment"],
                    description=t["description"],
                    trend_url=t["trend_url"],
                )
                insert_trend_history(
                    trend_name=t["trend_name"],
                    source_platform=t["source_platform"],
                    rank_at_time=t["rank_position"],
                    volume_at_time=t["volume"],
                    engagement_at_time=t["engagement_count"],
                    sentiment_at_time=t["sentiment"],
                )
                upsert_social_latest(
                    trend_name=t["trend_name"],
                    source_platform=t["source_platform"],
                    rank_position=t["rank_position"],
                    volume=t["volume"],
                    engagement_count=t["engagement_count"],
                    sentiment=t["sentiment"],
                    trend_url=t["trend_url"],
                )

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "UPDATE social_media_sources SET last_sync=%s WHERE id=%s",
                (now, src["id"])
            )
            cur.close()
            conn.close()

            print(f"[SOCIAL] {src['platform_name']} synced ({len(normalized)})")

        except Exception as e:
            print(f"[SOCIAL] {src['platform_name']} failed: {e}")


if __name__ == "__main__":
    sync_social_media()
