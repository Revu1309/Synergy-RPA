"""Unified menu configuration and helpers for dashboard navigation."""

from typing import Dict, List


MENU_ITEMS: List[Dict] = [
    {
        "section": "General",
        "items": [
            {"name": "Main Menu", "url": "/menu"},
            {"name": "UI Settings", "url": "/ui-settings"},
        ],
    },
    {
        "section": "Crypto",
        "items": [
            {"name": "Standard Dashboard", "url": "/asset-dashboard"},
            {"name": "Advanced Analytics", "url": "/advanced-crypto-dashboard"},
            {"name": "Manage Assets", "url": "/asset-management"},
            {"name": "Price Alerts", "url": "/crypto-alerts"},
        ],
    },
    {
        "section": "Weather",
        "items": [
            {"name": "Weather Dashboard", "url": "/weather-dashboard"},
            {"name": "Advanced Weather", "url": "/advanced-weather-dashboard"},
            {"name": "Manage Locations", "url": "/manage-locations"},
            {"name": "Weather Alerts", "url": "/weather-alerts"},
        ],
    },
    {
        "section": "Social Trends",
        "items": [
            {"name": "Trends Dashboard", "url": "/social-trends-dashboard"},
            {"name": "Advanced Trends", "url": "/advanced-social-trends-dashboard"},
            {"name": "Trend Alerts", "url": "/social-trend-alerts"},
        ],
    },
    {
        "section": "Signals & Monitoring",
        "items": [
            {"name": "Signal Fusion Report", "url": "/signal-fusion-report"},
            {"name": "Data Freshness Monitor", "url": "/data-freshness-monitor"},
        ],
    },
    {
        "section": "Administration",
        "items": [
            {"name": "User Management", "url": "/admin/users"},
            {"name": "Access Control", "url": "/admin/access-control"},
            {"name": "Alert Settings", "url": "/admin/alert-settings"},
        ],
    },
]


def _normalize_sections(sections: List[Dict]) -> List[Dict]:
    normalized = []
    for section in sections or []:
        items = section.get("items") or []
        clean_items = []
        for item in items:
            name = (item.get("name") or "").strip()
            url = (item.get("url") or "").strip()
            if not name or not url:
                continue
            clean_items.append({"name": name, "url": url})
        if clean_items:
            normalized.append({"section": section.get("section") or "Other", "items": clean_items})
    return normalized


def _flatten_urls(sections: List[Dict]) -> set:
    urls = set()
    for section in sections:
        for item in section.get("items", []):
            urls.add(item["url"])
    return urls


def merge_menu_with_db_modules(base_sections: List[Dict], db_modules: List[Dict]) -> List[Dict]:
    """
    Merge static menu config with database-driven module pages to avoid route omissions.
    DB pages are added when missing from static config.
    """
    merged = _normalize_sections(base_sections)
    seen_urls = _flatten_urls(merged)

    for module in db_modules or []:
        section_name = module.get("module_name") or module.get("module_key") or "Other"
        pages = module.get("pages") or []
        additions = []
        for page in pages:
            url = (page.get("route_path") or "").strip()
            name = (page.get("menu_label") or page.get("page_name") or url).strip()
            if not url or url in seen_urls:
                continue
            additions.append({"name": name, "url": url})
            seen_urls.add(url)
        if not additions:
            continue

        target = next((s for s in merged if s["section"].lower() == section_name.lower()), None)
        if target is None:
            merged.append({"section": section_name, "items": additions})
        else:
            target["items"].extend(additions)

    return merged
