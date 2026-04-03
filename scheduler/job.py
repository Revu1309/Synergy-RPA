from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
import logging
import os
from scraper.coinmarketcap import get_crypto_data
from database.models import insert_crypto_data, upsert_crypto_latest
from config.config import SCRAPE_INTERVAL_MINUTES, WEATHER_SYNC_INTERVAL_MINUTES, SOCIAL_SYNC_INTERVAL_MINUTES
from datetime import datetime, timedelta
from analysis.signal_fusion import compute_and_store_signal_fusion_index
from database.alert_models import evaluate_crypto_alerts, evaluate_social_trend_alerts

# Import the weather sync job defined in the dashboard module. The
# dashboard module no longer starts any schedulers on import, so this
# import is safe and allows the central scheduler to register the job.
from dashboard.app_new import sync_weather_job

def scrape_and_store():
    """Scrape crypto data and insert into database with proper timestamps."""
    start_ts = datetime.utcnow()
    logging.info(f"[CRYPTO] Job start: {start_ts.isoformat()}Z")
    try:
        data = get_crypto_data()
        inserted = 0
        for item in data:
            # Insert into historical table
            insert_crypto_data(
                item['symbol'],
                item['name'],
                item['price_usd'],
                item['market_cap'],
                item['volume_24h']
            )
            # Keep latest snapshot table in sync for read-only APIs/dashboards
            upsert_crypto_latest(
                item['symbol'],
                item['name'],
                item['price_usd'],
                item['market_cap'],
                item['volume_24h']
            )
            inserted += 1
        logging.info(f"[CRYPTO] Inserted {inserted} records")
    except Exception as e:
        logging.error(f"[CRYPTO] Error in scrape job: {e}")
    finally:
        try:
            fusion = compute_and_store_signal_fusion_index()
            logging.info(
                "[FUSION] Snapshot stored: fusion=%s (crypto=%s social=%s weather=%s, confidence=%s)",
                fusion.get("fusion_score"),
                fusion.get("crypto_score"),
                fusion.get("social_score"),
                fusion.get("weather_score"),
                fusion.get("confidence_level"),
            )
        except Exception as fusion_err:
            logging.error(f"[FUSION] Error computing/storing Signal Fusion Index: {fusion_err}")
        try:
            results = evaluate_crypto_alerts(trigger_source="scheduler", dispatch_notifications=True)
            triggered_count = len([r for r in results if r.get("is_match") and not r.get("in_cooldown")])
            logging.info("[ALERTS] Evaluated %d crypto alerts, %d newly triggered", len(results), triggered_count)
        except Exception as alert_err:
            logging.error(f"[ALERTS] Error evaluating crypto alerts: {alert_err}")
        end_ts = datetime.utcnow()
        logging.info(f"[CRYPTO] Job end: {end_ts.isoformat()}Z")

def sync_social_media_trends():
    """Scrape and store social media trends with proper timestamps."""
    start_ts = datetime.utcnow()
    logging.info(f"[SOCIAL] Job start: {start_ts.isoformat()}Z")
    try:
        from scraper.social_media import sync_social_media
        
        # Sync social media data from all sources
        sync_social_media()

        logging.info(f"[SOCIAL] Social media trends sync complete")
    except Exception as e:
        logging.error(f"[SOCIAL] Error syncing social media trends: {e}")
    finally:
        try:
            results = evaluate_social_trend_alerts(trigger_source="scheduler", dispatch_notifications=True)
            triggered_count = len([r for r in results if r.get("is_match") and not r.get("in_cooldown")])
            logging.info("[ALERTS] Evaluated %d social alerts, %d newly triggered", len(results), triggered_count)
        except Exception as alert_err:
            logging.error(f"[ALERTS] Error evaluating social alerts: {alert_err}")
        end_ts = datetime.utcnow()
        logging.info(f"[SOCIAL] Job end: {end_ts.isoformat()}Z")

def start_scheduler():
    """Start the scheduler."""
    scheduler = BlockingScheduler()

    # Initial crypto scrape - run in 3 seconds
    crypto_run_time = datetime.now() + timedelta(seconds=3)
    scheduler.add_job(scrape_and_store, trigger=DateTrigger(run_date=crypto_run_time), id='initial_scrape')

    # Initial social media sync - run in 8 seconds (after crypto)
    social_media_run_time = datetime.now() + timedelta(seconds=8)
    scheduler.add_job(sync_social_media_trends, trigger=DateTrigger(run_date=social_media_run_time), id='initial_social_media_sync')

    # Then run crypto every SCRAPE_INTERVAL_MINUTES
    interval_trigger = IntervalTrigger(minutes=SCRAPE_INTERVAL_MINUTES)
    scheduler.add_job(scrape_and_store, trigger=interval_trigger, id='scrape_job')

    # Social media trends sync - configured interval
    try:
        social_interval = int(os.getenv('SOCIAL_SYNC_INTERVAL_MINUTES', SOCIAL_SYNC_INTERVAL_MINUTES))
    except Exception:
        social_interval = SOCIAL_SYNC_INTERVAL_MINUTES
    social_media_trigger = IntervalTrigger(minutes=social_interval)
    scheduler.add_job(sync_social_media_trends, trigger=social_media_trigger, id='social_media_sync')

    # Weather sync interval: read from environment or config
    try:
        weather_interval = int(os.getenv('WEATHER_SYNC_INTERVAL_MINUTES', WEATHER_SYNC_INTERVAL_MINUTES))
    except Exception:
        weather_interval = WEATHER_SYNC_INTERVAL_MINUTES

    # Schedule weather sync: initial run shortly after start, then interval
    weather_initial = datetime.now() + timedelta(seconds=10)
    scheduler.add_job(sync_weather_job, trigger=DateTrigger(run_date=weather_initial), id='initial_weather_sync')
    weather_trigger = IntervalTrigger(minutes=weather_interval)
    scheduler.add_job(sync_weather_job, trigger=weather_trigger, id='weather_sync_job', replace_existing=True, max_instances=1)

    logging.info(
        f"Scheduler started. Crypto every {SCRAPE_INTERVAL_MINUTES} min, "
        f"Social media every {social_interval} min, Weather every {weather_interval} min."
    )
    scheduler.start()
