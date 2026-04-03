#!/usr/bin/env python3
"""
RPA Project: Extract crypto data from CoinMarketCap and store in MySQL.
"""

import os
import logging
import socket
import subprocess
import sys
import time

BASE_DIR = os.path.dirname(__file__)

# Add project virtual environment site-packages to path when available.
for env_dir in (".venv", "venv"):
    site_packages = os.path.join(BASE_DIR, env_dir, "Lib", "site-packages")
    if os.path.exists(site_packages) and site_packages not in sys.path:
        sys.path.insert(0, site_packages)
        break

from dotenv import load_dotenv
from config.config import (
    SCRAPE_INTERVAL_MINUTES,
    SOCIAL_SYNC_INTERVAL_MINUTES,
    WEATHER_SYNC_INTERVAL_MINUTES,
)
from database.connection import create_table
from database.access_control import create_access_control_tables, seed_default_access_config
from scheduler.job import start_scheduler
from utils.logger import setup_logging

logger = logging.getLogger(__name__)


def resolve_python_executable():
    """Resolve python executable from .venv/venv with system fallback."""
    for env_dir in (".venv", "venv"):
        candidate = os.path.join(BASE_DIR, env_dir, "Scripts", "python.exe")
        if os.path.exists(candidate):
            return candidate
    fallback = sys.executable or "python"
    return fallback


def run_dashboard(host: str, port: int):
    """Run the Flask dashboard in a separate process and return process handle."""
    try:
        # Prefer the newer dashboard implementation when available.
        dashboard_new_path = os.path.join(BASE_DIR, "dashboard", "app_new.py")
        dashboard_legacy_path = os.path.join(BASE_DIR, "dashboard", "app.py")
        dashboard_path = dashboard_new_path if os.path.exists(dashboard_new_path) else dashboard_legacy_path
        python_exe = resolve_python_executable()

        env = os.environ.copy()
        env["PYTHONPATH"] = BASE_DIR
        env.setdefault("FLASK_RUN_HOST", host)
        env.setdefault("FLASK_RUN_PORT", str(port))
        if python_exe == (sys.executable or "python"):
            logger.info("Virtual environment not found; using '%s'", python_exe)
        else:
            logger.info("Starting dashboard with '%s'", python_exe)

        process = subprocess.Popen(
            [python_exe, dashboard_path],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return process
    except Exception as e:
        logger.exception("Error starting dashboard: %s", e)
        return None


def maybe_refresh_timestamps():
    """Refresh timestamps if helper exists; skip silently when absent."""
    try:
        from scripts.refresh_timestamps import refresh_all_timestamps
    except Exception:
        return

    try:
        refresh_all_timestamps(spacing_seconds=1)
    except Exception as e:
        logger.warning("Timestamp refresh failed: %s", e)


def wait_for_dashboard_startup(process: subprocess.Popen, host: str, port: int, timeout_seconds: int = 10):
    """Wait for dashboard process and TCP port to become available."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if process.poll() is not None:
            return False, "dashboard process exited early"

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.settimeout(0.5)
            if sock.connect_ex((host, port)) == 0:
                return True, "dashboard reachable"
        finally:
            sock.close()
        time.sleep(0.3)
    return False, f"dashboard not reachable on {host}:{port} after {timeout_seconds}s"


def run_with_retries(name: str, func, retries: int = 3, base_delay: float = 1.0):
    """Run bootstrap function with simple retry/backoff for transient failures."""
    for attempt in range(1, retries + 1):
        try:
            func()
            if attempt > 1:
                logger.info("%s succeeded on retry %d", name, attempt)
            return True
        except Exception as e:
            if attempt == retries:
                logger.error("%s failed after %d attempts: %s", name, retries, e)
                return False
            delay = base_delay * attempt
            logger.warning("%s failed (attempt %d/%d): %s; retrying in %.1fs", name, attempt, retries, e, delay)
            time.sleep(delay)


def bootstrap_database():
    """Create core and snapshot database tables."""
    created_core = run_with_retries("create_table", create_table, retries=3, base_delay=1.5)
    if not created_core:
        logger.error("Database core tables could not be created; exiting.")
        sys.exit(1)

    try:
        create_access_control_tables()
        seed_default_access_config()
    except Exception as e:
        logger.warning("Access control table setup failed: %s", e)

    try:
        from database.connection import (
            create_crypto_latest_table,
            create_weather_latest_table,
            create_social_latest_table,
            create_signal_fusion_index_table,
        )
        run_with_retries("create_crypto_latest_table", create_crypto_latest_table, retries=2, base_delay=1.0)
        run_with_retries("create_weather_latest_table", create_weather_latest_table, retries=2, base_delay=1.0)
        run_with_retries("create_social_latest_table", create_social_latest_table, retries=2, base_delay=1.0)
        run_with_retries("create_signal_fusion_index_table", create_signal_fusion_index_table, retries=2, base_delay=1.0)
    except ImportError as e:
        logger.warning("Latest snapshot table setup unavailable: %s", e)
    except Exception as e:
        logger.warning("Could not create latest snapshot tables: %s", e)


def create_optional_tables():
    """Create optional feature tables."""
    try:
        from database.social_media_models import create_social_trends_tables
        create_social_trends_tables()
    except ImportError as e:
        logger.info("Social trends table module not available: %s", e)
    except Exception as e:
        logger.info("Social media tables may already exist or failed to create: %s", e)

    try:
        from database.alert_models import create_alerts_table, create_weather_alerts_table, create_social_trend_alerts_table
        create_alerts_table()
        create_weather_alerts_table()
        create_social_trend_alerts_table()
    except ImportError as e:
        logger.info("Alerts table module not available: %s", e)
    except Exception as e:
        logger.info("Alerts table creation may have failed: %s", e)

    try:
        from database.ui_settings import create_ui_settings_table
        create_ui_settings_table()
    except ImportError as e:
        logger.info("UI settings table module not available: %s", e)
    except Exception as e:
        logger.info("UI settings table creation may have failed: %s", e)


def main():
    """Main entry point."""
    load_dotenv()
    setup_logging()
    dashboard_host = os.getenv("DASHBOARD_HOST", "127.0.0.1")
    dashboard_port = int(os.getenv("DASHBOARD_PORT", "5000"))

    logger.info("Starting RPA bootstrap")
    logger.info("Python executable: %s", resolve_python_executable())
    logger.info("Dashboard target: http://%s:%d", dashboard_host, dashboard_port)

    bootstrap_database()

    maybe_refresh_timestamps()
    create_optional_tables()

    logger.info("Starting RPA System")
    logger.info("Dashboard will be available at: http://%s:%d", dashboard_host, dashboard_port)
    logger.info("Crypto data collection runs every %s minute(s)", SCRAPE_INTERVAL_MINUTES)
    logger.info("Social media trends sync every %s minute(s)", SOCIAL_SYNC_INTERVAL_MINUTES)
    logger.info("Weather sync runs every %s minute(s)", WEATHER_SYNC_INTERVAL_MINUTES)
    logger.info("Press Ctrl+C to stop all services")

    dashboard_process = run_dashboard(dashboard_host, dashboard_port)
    if dashboard_process is None:
        logger.warning("Continuing without dashboard process.")
    else:
        ready, detail = wait_for_dashboard_startup(dashboard_process, dashboard_host, dashboard_port, timeout_seconds=12)
        if ready:
            logger.info("Dashboard health check passed: %s", detail)
        else:
            logger.warning("Dashboard health check failed: %s", detail)

    try:
        start_scheduler()
    except KeyboardInterrupt:
        logger.info("Shutting down RPA System...")
    finally:
        if dashboard_process is not None and dashboard_process.poll() is None:
            logger.info("Stopping dashboard process (pid=%s)", dashboard_process.pid)
            dashboard_process.terminate()
            try:
                dashboard_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Dashboard did not stop in time; killing process.")
                dashboard_process.kill()
        sys.exit(0)


if __name__ == "__main__":
    main()
