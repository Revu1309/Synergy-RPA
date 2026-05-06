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
from utils.data_service import DataService, DataValidationError
from utils.realtime_data import get_realtime_cache

# Import the weather sync job defined in the dashboard module. The
# dashboard module no longer starts any schedulers on import, so this
# import is safe and allows the central scheduler to register the job.
from dashboard.app_new import sync_weather_job

def scrape_and_store():
    """Scrape crypto data and insert into database with proper timestamps and real-time updates."""
    start_ts = datetime.utcnow()
    logging.info(f"[CRYPTO] Job start: {start_ts.isoformat()}Z")
    cache = get_realtime_cache()
    
    try:
        raw_data = get_crypto_data()
        
        # Normalize and validate data
        try:
            normalized_data = DataService.CRYPTO.normalize_crypto_list(raw_data)
        except Exception as normalize_err:
            logging.warning(f"[CRYPTO] Data normalization warning: {normalize_err}")
            normalized_data = raw_data
        
        inserted = 0
        for item in normalized_data:
            try:
                # Insert into historical table
                insert_crypto_data(
                    item['symbol'],
                    item['name'],
                    item['price_usd'],
                    item.get('market_cap'),
                    item.get('volume_24h')
                )
                # Keep latest snapshot table in sync for read-only APIs/dashboards
                upsert_crypto_latest(
                    item['symbol'],
                    item['name'],
                    item['price_usd'],
                    item.get('market_cap'),
                    item.get('volume_24h')
                )
                inserted += 1
            except Exception as item_err:
                logging.warning(f"[CRYPTO] Failed to insert {item.get('symbol')}: {item_err}")
        
        # Update real-time cache
        try:
            cache.update_crypto(normalized_data)
            logging.info(f"[CRYPTO] Cache updated with {len(normalized_data)} assets")
        except Exception as cache_err:
            logging.warning(f"[CRYPTO] Failed to update cache: {cache_err}")
        
        logging.info(f"[CRYPTO] Inserted {inserted} records")
        
    except Exception as e:
        logging.error(f"[CRYPTO] Error in scrape job: {e}")
    finally:
        try:
            fusion = compute_and_store_signal_fusion_index()
            # Update cache with fusion data
            try:
                cache.update_signal_fusion(fusion)
            except Exception as cache_err:
                logging.warning(f"[FUSION] Failed to update cache: {cache_err}")
            
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
    """Scrape and store social media trends with proper timestamps and real-time updates."""
    start_ts = datetime.utcnow()
    logging.info(f"[SOCIAL] Job start: {start_ts.isoformat()}Z")
    cache = get_realtime_cache()
    
    try:
        from scraper.social_media import sync_social_media
        
        # Sync social media data from all sources
        raw_data = sync_social_media()
        
        # Normalize and validate data
        try:
            if raw_data:
                normalized_data = DataService.SOCIAL_TRENDS.normalize_trend_list(
                    raw_data if isinstance(raw_data, list) else [raw_data]
                )
                # Update cache
                cache.update_social_trends(normalized_data)
                logging.info(f"[SOCIAL] Cache updated with {len(normalized_data)} trends")
        except Exception as normalize_err:
            logging.warning(f"[SOCIAL] Data normalization warning: {normalize_err}")

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
