import sys
from pathlib import Path

# add project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from weather_sync import sync_weather_job

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

from scraper.coinmarketcap import get_crypto_data
from weather_sync import sync_weather_job   # ✅ FIX
from scraper.social_media import sync_social_media


def start_scheduler():
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        get_crypto_data,
        trigger=IntervalTrigger(minutes=1),
        id="crypto_sync",
        replace_existing=True,
        max_instances=1
    )

    scheduler.add_job(
        sync_weather_job,
        trigger=IntervalTrigger(minutes=1),
        id="weather_sync",
        replace_existing=True,
        max_instances=1
    )

    scheduler.add_job(
        sync_social_media,
        trigger=IntervalTrigger(minutes=1),
        id="social_media_sync",
        replace_existing=True,
        max_instances=1
    )

    scheduler.start()
    print(f"[SCHEDULER] Started at {datetime.utcnow().isoformat()}Z")
