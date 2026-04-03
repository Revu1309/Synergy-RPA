import json
import logging
from datetime import datetime, timedelta

import requests

from .connection import create_connection


logger = logging.getLogger(__name__)


# ==================== CRYPTO ALERTS ====================

SUPPORTED_NOTIFY_METHODS = {"console", "telegram", "discord_webhook", "email"}
SUPPORTED_CUSTOM_METRICS = {"price_usd", "price_change_pct"}


def _safe_json_loads(value, default=None):
    if default is None:
        default = {}
    if not value:
        return default
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


def _to_iso(value):
    return value.isoformat() if value is not None else None


def _compare_value(condition, left_value, threshold):
    if condition == "gt":
        return left_value > threshold
    if condition == "lt":
        return left_value < threshold
    if condition == "eq":
        return abs(left_value - threshold) < 1e-12
    return False


def create_alerts_table():
    conn = create_connection()
    if not conn:
        print("Failed to create alerts table: DB connection failed")
        return

    cur = conn.cursor()
    try:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS crypto_alerts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                `condition` ENUM('gt','lt','eq') NOT NULL,
                threshold DECIMAL(30,8) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                notify_method VARCHAR(50) DEFAULT 'console',
                description TEXT,
                alert_mode VARCHAR(20) DEFAULT 'standard',
                custom_metric VARCHAR(50) NULL,
                custom_config TEXT NULL,
                cooldown_minutes INT DEFAULT 15,
                is_triggered BOOLEAN DEFAULT FALSE,
                last_trigger_message TEXT NULL,
                last_evaluated TIMESTAMP NULL,
                last_triggered TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_symbol (symbol),
                INDEX idx_active (is_active),
                INDEX idx_alert_mode (alert_mode)
            )
        """
        )

        alter_statements = [
            "ALTER TABLE crypto_alerts MODIFY `condition` ENUM('gt','lt','eq') NOT NULL",
            "ALTER TABLE crypto_alerts ADD COLUMN alert_mode VARCHAR(20) DEFAULT 'standard'",
            "ALTER TABLE crypto_alerts ADD COLUMN custom_metric VARCHAR(50) NULL",
            "ALTER TABLE crypto_alerts ADD COLUMN custom_config TEXT NULL",
            "ALTER TABLE crypto_alerts ADD COLUMN cooldown_minutes INT DEFAULT 15",
            "ALTER TABLE crypto_alerts ADD COLUMN is_triggered BOOLEAN DEFAULT FALSE",
            "ALTER TABLE crypto_alerts ADD COLUMN last_trigger_message TEXT NULL",
            "ALTER TABLE crypto_alerts ADD COLUMN last_evaluated TIMESTAMP NULL",
            "ALTER TABLE crypto_alerts ADD INDEX idx_alert_mode (alert_mode)",
        ]
        for stmt in alter_statements:
            try:
                cur.execute(stmt)
            except Exception:
                pass

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS alert_notification_channels (
                id INT AUTO_INCREMENT PRIMARY KEY,
                channel_key VARCHAR(50) NOT NULL UNIQUE,
                module_key VARCHAR(20) NOT NULL DEFAULT 'all',
                channel_type VARCHAR(50) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                config_json TEXT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_module_key (module_key),
                INDEX idx_channel_type (channel_type),
                INDEX idx_channel_active (is_active)
            )
        """
        )
        for stmt in [
            "ALTER TABLE alert_notification_channels ADD COLUMN module_key VARCHAR(20) NOT NULL DEFAULT 'all'",
            "ALTER TABLE alert_notification_channels ADD INDEX idx_module_key (module_key)",
        ]:
            try:
                cur.execute(stmt)
            except Exception:
                pass

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS crypto_alert_events (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                alert_id INT NOT NULL,
                symbol VARCHAR(20) NOT NULL,
                event_type VARCHAR(30) NOT NULL,
                message TEXT,
                observed_price DECIMAL(30,8) NULL,
                metric_value DECIMAL(30,8) NULL,
                payload_json TEXT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_alert_id (alert_id),
                INDEX idx_symbol (symbol),
                INDEX idx_event_type (event_type),
                INDEX idx_created_at (created_at)
            )
        """
        )

        cur.execute(
            """
            INSERT INTO alert_notification_channels (channel_key, module_key, channel_type, is_active, config_json)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE channel_type = VALUES(channel_type), is_active = VALUES(is_active)
        """,
            ("console_default", "all", "console", True, "{}"),
        )

        conn.commit()
        print("crypto_alerts and alert support tables ensured")
    finally:
        cur.close()
        conn.close()


def insert_alert(
    symbol,
    condition,
    threshold,
    is_active=True,
    notify_method="console",
    description=None,
    alert_mode="standard",
    custom_metric=None,
    custom_config=None,
    cooldown_minutes=15,
):
    if notify_method not in SUPPORTED_NOTIFY_METHODS:
        notify_method = "console"
    if alert_mode not in ("standard", "custom"):
        alert_mode = "standard"
    if custom_metric and custom_metric not in SUPPORTED_CUSTOM_METRICS:
        custom_metric = None

    custom_config_json = json.dumps(custom_config or {})

    conn = create_connection()
    if not conn:
        return False
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO crypto_alerts
            (symbol, `condition`, threshold, is_active, notify_method, description, alert_mode, custom_metric, custom_config, cooldown_minutes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
            (
                symbol,
                condition,
                threshold,
                is_active,
                notify_method,
                description,
                alert_mode,
                custom_metric,
                custom_config_json,
                cooldown_minutes,
            ),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error inserting alert: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def get_alerts():
    conn = create_connection()
    if not conn:
        return []
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, symbol, `condition`, threshold, is_active, notify_method, description,
                   alert_mode, custom_metric, custom_config, cooldown_minutes,
                   is_triggered, last_trigger_message, last_evaluated, last_triggered, created_at, updated_at
            FROM crypto_alerts
            ORDER BY id DESC
        """
        )
        rows = cur.fetchall()
        alerts = []
        for r in rows:
            alerts.append(
                {
                    "id": r[0],
                    "symbol": r[1],
                    "condition": r[2],
                    "threshold": float(r[3]) if r[3] is not None else None,
                    "is_active": bool(r[4]),
                    "notify_method": r[5],
                    "description": r[6],
                    "alert_mode": r[7] or "standard",
                    "custom_metric": r[8],
                    "custom_config": _safe_json_loads(r[9], {}),
                    "cooldown_minutes": int(r[10]) if r[10] is not None else 15,
                    "is_triggered": bool(r[11]),
                    "last_trigger_message": r[12],
                    "last_evaluated": _to_iso(r[13]),
                    "last_triggered": _to_iso(r[14]),
                    "created_at": _to_iso(r[15]),
                    "updated_at": _to_iso(r[16]),
                }
            )
        return alerts
    except Exception as e:
        print(f"Error fetching alerts: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def delete_alert(alert_id):
    conn = create_connection()
    if not conn:
        return False
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM crypto_alerts WHERE id = %s", (alert_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting alert: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def get_active_alerts():
    conn = create_connection()
    if not conn:
        return []
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, symbol, `condition`, threshold, notify_method, description, last_triggered,
                   alert_mode, custom_metric, custom_config, cooldown_minutes,
                   is_triggered, last_trigger_message, last_evaluated
            FROM crypto_alerts
            WHERE is_active = TRUE
        """
        )
        rows = cur.fetchall()
        alerts = []
        for r in rows:
            alerts.append(
                {
                    "id": r[0],
                    "symbol": r[1],
                    "condition": r[2],
                    "threshold": float(r[3]) if r[3] is not None else None,
                    "notify_method": r[4],
                    "description": r[5],
                    "last_triggered": _to_iso(r[6]),
                    "alert_mode": r[7] or "standard",
                    "custom_metric": r[8],
                    "custom_config": _safe_json_loads(r[9], {}),
                    "cooldown_minutes": int(r[10]) if r[10] is not None else 15,
                    "is_triggered": bool(r[11]),
                    "last_trigger_message": r[12],
                    "last_evaluated": _to_iso(r[13]),
                }
            )
        return alerts
    except Exception as e:
        print(f"Error fetching active alerts: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def get_latest_price(symbol):
    conn = create_connection()
    if not conn:
        return None
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT price_usd, last_updated FROM crypto_latest WHERE symbol = %s LIMIT 1",
            (symbol,),
        )
        r = cur.fetchone()
        if r:
            return {"price_usd": float(r[0]), "timestamp": _to_iso(r[1])}

        cur.execute(
            "SELECT price_usd, timestamp FROM crypto_assets WHERE symbol = %s ORDER BY timestamp DESC LIMIT 1",
            (symbol,),
        )
        r = cur.fetchone()
        if not r:
            return None
        return {"price_usd": float(r[0]), "timestamp": _to_iso(r[1])}
    except Exception as e:
        print(f"Error getting latest price for {symbol}: {e}")
        return None
    finally:
        cur.close()
        conn.close()


def get_price_history(symbol, limit=50):
    conn = create_connection()
    if not conn:
        return []
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT price_usd, timestamp FROM crypto_assets WHERE symbol = %s ORDER BY timestamp DESC LIMIT %s",
            (symbol, limit),
        )
        rows = cur.fetchall()
        rows = list(reversed(rows))
        return [{"price_usd": float(r[0]), "timestamp": _to_iso(r[1])} for r in rows]
    except Exception as e:
        print(f"Error getting history for {symbol}: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def get_price_minutes_ago(symbol, minutes=60):
    conn = create_connection()
    if not conn:
        return None
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT price_usd, timestamp
            FROM crypto_assets
            WHERE symbol = %s
              AND timestamp <= DATE_SUB(UTC_TIMESTAMP(), INTERVAL %s MINUTE)
            ORDER BY timestamp DESC
            LIMIT 1
        """,
            (symbol, minutes),
        )
        r = cur.fetchone()
        if not r:
            return None
        return {"price_usd": float(r[0]), "timestamp": _to_iso(r[1])}
    except Exception as e:
        print(f"Error getting {minutes}m-back price for {symbol}: {e}")
        return None
    finally:
        cur.close()
        conn.close()


def insert_crypto_alert_event(
    alert_id,
    symbol,
    event_type,
    message=None,
    observed_price=None,
    metric_value=None,
    payload=None,
):
    conn = create_connection()
    if not conn:
        return False
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO crypto_alert_events
            (alert_id, symbol, event_type, message, observed_price, metric_value, payload_json)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """,
            (
                alert_id,
                symbol,
                event_type,
                message,
                observed_price,
                metric_value,
                json.dumps(payload or {}),
            ),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error inserting crypto alert event: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def get_crypto_alert_events(limit=100):
    conn = create_connection()
    if not conn:
        return []
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, alert_id, symbol, event_type, message, observed_price, metric_value, payload_json, created_at
            FROM crypto_alert_events
            ORDER BY id DESC
            LIMIT %s
        """,
            (limit,),
        )
        rows = cur.fetchall()
        return [
            {
                "id": r[0],
                "alert_id": r[1],
                "symbol": r[2],
                "event_type": r[3],
                "message": r[4],
                "observed_price": float(r[5]) if r[5] is not None else None,
                "metric_value": float(r[6]) if r[6] is not None else None,
                "payload": _safe_json_loads(r[7], {}),
                "created_at": _to_iso(r[8]),
            }
            for r in rows
        ]
    except Exception as e:
        print(f"Error fetching crypto alert events: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def get_notification_channels(module_key=None):
    conn = create_connection()
    if not conn:
        return []
    cur = conn.cursor()
    try:
        if module_key:
            cur.execute(
                """
                SELECT id, channel_key, module_key, channel_type, is_active, config_json, created_at, updated_at
                FROM alert_notification_channels
                WHERE module_key = %s
                ORDER BY id DESC
                """,
                (module_key,),
            )
        else:
            cur.execute(
                """
                SELECT id, channel_key, module_key, channel_type, is_active, config_json, created_at, updated_at
                FROM alert_notification_channels
                ORDER BY id DESC
                """
            )
        rows = cur.fetchall()
        return [
            {
                "id": r[0],
                "channel_key": r[1],
                "module_key": r[2] or "all",
                "channel_type": r[3],
                "is_active": bool(r[4]),
                "config": _safe_json_loads(r[5], {}),
                "created_at": _to_iso(r[6]),
                "updated_at": _to_iso(r[7]),
            }
            for r in rows
        ]
    except Exception as e:
        print(f"Error reading notification channels: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def upsert_notification_channel(channel_key, channel_type, is_active=True, config=None, module_key="all"):
    conn = create_connection()
    if not conn:
        return False
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO alert_notification_channels (channel_key, module_key, channel_type, is_active, config_json)
            VALUES (%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                module_key = VALUES(module_key),
                channel_type = VALUES(channel_type),
                is_active = VALUES(is_active),
                config_json = VALUES(config_json),
                updated_at = CURRENT_TIMESTAMP
        """,
            (channel_key, module_key, channel_type, is_active, json.dumps(config or {})),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error upserting notification channel: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def _get_notification_channel_config(channel_type, module_key="all"):
    conn = create_connection()
    if not conn:
        return None
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT config_json
            FROM alert_notification_channels
            WHERE channel_type = %s AND is_active = TRUE AND module_key IN (%s, 'all')
            ORDER BY CASE WHEN module_key = %s THEN 0 ELSE 1 END, updated_at DESC
            LIMIT 1
        """,
            (channel_type, module_key, module_key),
        )
        row = cur.fetchone()
        if not row:
            return None
        return _safe_json_loads(row[0], {})
    except Exception:
        return None
    finally:
        cur.close()
        conn.close()

def _send_telegram_notification(message, module_key="all"):
    cfg = _get_notification_channel_config("telegram", module_key=module_key) or {}
    token = cfg.get("bot_token")
    chat_id = cfg.get("chat_id")
    if not token or not chat_id:
        return False, "telegram config missing bot_token/chat_id"
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message},
            timeout=8,
        )
        if resp.status_code >= 400:
            return False, f"telegram send failed ({resp.status_code})"
        return True, "sent"
    except Exception as e:
        return False, f"telegram send exception: {e}"


def _send_discord_webhook_notification(message, module_key="all"):
    cfg = _get_notification_channel_config("discord_webhook", module_key=module_key) or {}
    webhook_url = cfg.get("webhook_url")
    if not webhook_url:
        return False, "discord webhook config missing webhook_url"
    try:
        resp = requests.post(webhook_url, json={"content": message}, timeout=8)
        if resp.status_code >= 400:
            return False, f"discord webhook send failed ({resp.status_code})"
        return True, "sent"
    except Exception as e:
        return False, f"discord webhook send exception: {e}"


def send_alert_notification(alert, message, module_key="all"):
    method = (alert.get("notify_method") or "console").lower()
    if method == "console" or method == "email":
        logger.warning("[ALERT][%s] %s", alert.get("symbol"), message)
        return True, "logged"
    if method == "telegram":
        return _send_telegram_notification(message, module_key=module_key)
    if method == "discord_webhook":
        return _send_discord_webhook_notification(message, module_key=module_key)
    logger.warning("[ALERT][%s] unknown notify method '%s': %s", alert.get("symbol"), method, message)
    return False, f"unknown notify method: {method}"


def _evaluate_metric(alert, current_price):
    mode = alert.get("alert_mode", "standard")
    custom_metric = alert.get("custom_metric")
    config = alert.get("custom_config") or {}
    symbol = alert.get("symbol")

    if mode != "custom" or not custom_metric or custom_metric == "price_usd":
        return current_price, "price_usd"

    if custom_metric == "price_change_pct":
        lookback_minutes = int(config.get("lookback_minutes", 60))
        old_price = get_price_minutes_ago(symbol, minutes=lookback_minutes)
        if not old_price or old_price["price_usd"] in (None, 0):
            return None, f"price_change_pct_{lookback_minutes}m"
        pct = ((current_price - old_price["price_usd"]) / old_price["price_usd"]) * 100.0
        return pct, f"price_change_pct_{lookback_minutes}m"

    return None, custom_metric


def _within_cooldown(last_triggered_iso, cooldown_minutes):
    if not last_triggered_iso:
        return False
    try:
        last_triggered = datetime.fromisoformat(last_triggered_iso.replace("Z", "+00:00"))
        now = datetime.utcnow().replace(tzinfo=last_triggered.tzinfo)
        return now < (last_triggered + timedelta(minutes=cooldown_minutes))
    except Exception:
        return False


def update_alert_state(alert_id, is_triggered, message, triggered_now=False):
    conn = create_connection()
    if not conn:
        return False
    cur = conn.cursor()
    try:
        if triggered_now:
            cur.execute(
                """
                UPDATE crypto_alerts
                SET is_triggered = %s,
                    last_trigger_message = %s,
                    last_evaluated = UTC_TIMESTAMP(),
                    last_triggered = UTC_TIMESTAMP()
                WHERE id = %s
            """,
                (is_triggered, message, alert_id),
            )
        else:
            cur.execute(
                """
                UPDATE crypto_alerts
                SET is_triggered = %s,
                    last_trigger_message = %s,
                    last_evaluated = UTC_TIMESTAMP()
                WHERE id = %s
            """,
                (is_triggered, message, alert_id),
            )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating alert state: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def evaluate_crypto_alerts(trigger_source="scheduler", dispatch_notifications=True):
    alerts = get_active_alerts()
    evaluated = []

    for alert in alerts:
        symbol = alert["symbol"]
        latest = get_latest_price(symbol)
        if not latest:
            message = "No current price available"
            update_alert_state(alert["id"], False, message, triggered_now=False)
            evaluated.append({**alert, "is_match": False, "state_message": message})
            continue

        current_price = latest["price_usd"]
        metric_value, metric_name = _evaluate_metric(alert, current_price)
        if metric_value is None:
            message = f"Metric unavailable ({metric_name})"
            update_alert_state(alert["id"], False, message, triggered_now=False)
            evaluated.append({**alert, "is_match": False, "state_message": message, "current_price": current_price})
            continue

        threshold = float(alert["threshold"])
        is_match = _compare_value(alert["condition"], metric_value, threshold)
        cooldown_minutes = int(alert.get("cooldown_minutes") or 15)
        in_cooldown = _within_cooldown(alert.get("last_triggered"), cooldown_minutes)

        state_message = (
            f"{metric_name}={metric_value:.6f} {alert['condition']} {threshold:.6f} "
            f"(current_price={current_price:.6f})"
        )

        if is_match and not in_cooldown:
            notify_message = f"[CRYPTO ALERT] {symbol}: {state_message}"
            sent_ok = True
            sent_status = "skipped"
            if dispatch_notifications:
                sent_ok, sent_status = send_alert_notification(alert, notify_message, module_key="crypto")

            update_alert_state(alert["id"], True, state_message, triggered_now=True)
            insert_crypto_alert_event(
                alert["id"],
                symbol,
                "triggered",
                message=f"{state_message} | notify={sent_status}",
                observed_price=current_price,
                metric_value=metric_value,
                payload={
                    "trigger_source": trigger_source,
                    "notify_method": alert.get("notify_method"),
                    "sent_ok": sent_ok,
                    "sent_status": sent_status,
                },
            )
        elif is_match and in_cooldown:
            message = f"{state_message} | in cooldown ({cooldown_minutes}m)"
            update_alert_state(alert["id"], True, message, triggered_now=False)
            insert_crypto_alert_event(
                alert["id"],
                symbol,
                "cooldown",
                message=message,
                observed_price=current_price,
                metric_value=metric_value,
                payload={"trigger_source": trigger_source},
            )
        else:
            was_triggered = bool(alert.get("is_triggered"))
            update_alert_state(alert["id"], False, state_message, triggered_now=False)
            if was_triggered:
                insert_crypto_alert_event(
                    alert["id"],
                    symbol,
                    "resolved",
                    message=state_message,
                    observed_price=current_price,
                    metric_value=metric_value,
                    payload={"trigger_source": trigger_source},
                )

        evaluated.append(
            {
                **alert,
                "is_match": is_match,
                "metric_name": metric_name,
                "metric_value": metric_value,
                "current_price": current_price,
                "state_message": state_message,
                "in_cooldown": in_cooldown,
            }
        )
    return evaluated


# ==================== WEATHER ALERTS ====================


def create_weather_alerts_table():
    conn = create_connection()
    if not conn:
        print('Failed to create weather alerts table: DB connection failed')
        return
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS weather_alerts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            location_name VARCHAR(100) NOT NULL,
            alert_type VARCHAR(50) NOT NULL,
            `condition` ENUM('gt','lt','eq') NOT NULL,
            threshold DECIMAL(10,2) NOT NULL,
            metric_type VARCHAR(50) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            notify_method VARCHAR(50) DEFAULT 'console',
            description TEXT,
            alert_mode VARCHAR(20) DEFAULT 'standard',
            custom_config TEXT NULL,
            cooldown_minutes INT DEFAULT 15,
            is_triggered BOOLEAN DEFAULT FALSE,
            last_trigger_message TEXT NULL,
            last_evaluated TIMESTAMP NULL,
            last_triggered TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_location (location_name),
            INDEX idx_active (is_active),
            INDEX idx_metric (metric_type)
        )
    """)
    for stmt in [
        "ALTER TABLE weather_alerts ADD COLUMN alert_mode VARCHAR(20) DEFAULT 'standard'",
        "ALTER TABLE weather_alerts ADD COLUMN custom_config TEXT NULL",
        "ALTER TABLE weather_alerts ADD COLUMN cooldown_minutes INT DEFAULT 15",
        "ALTER TABLE weather_alerts ADD COLUMN is_triggered BOOLEAN DEFAULT FALSE",
        "ALTER TABLE weather_alerts ADD COLUMN last_trigger_message TEXT NULL",
        "ALTER TABLE weather_alerts ADD COLUMN last_evaluated TIMESTAMP NULL",
    ]:
        try:
            cur.execute(stmt)
        except Exception:
            pass

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS weather_alert_events (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            alert_id INT NOT NULL,
            location_name VARCHAR(100) NOT NULL,
            event_type VARCHAR(30) NOT NULL,
            message TEXT,
            metric_type VARCHAR(50),
            metric_value DECIMAL(20,6) NULL,
            payload_json TEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_alert_id (alert_id),
            INDEX idx_location (location_name),
            INDEX idx_event_type (event_type),
            INDEX idx_created_at (created_at)
        )
    """
    )
    conn.commit()
    cur.close()
    conn.close()
    print('weather_alerts table ensured')


def insert_weather_alert(
    location_name,
    alert_type,
    condition,
    threshold,
    metric_type,
    is_active=True,
    notify_method='console',
    description=None,
    alert_mode="standard",
    custom_config=None,
    cooldown_minutes=15,
):
    conn = create_connection()
    if not conn:
        return False
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO weather_alerts
            (location_name, alert_type, `condition`, threshold, metric_type, is_active, notify_method, description, alert_mode, custom_config, cooldown_minutes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                location_name,
                alert_type,
                condition,
                threshold,
                metric_type,
                is_active,
                notify_method,
                description,
                alert_mode,
                json.dumps(custom_config or {}),
                cooldown_minutes,
            ),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error inserting weather alert: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def get_weather_alerts():
    conn = create_connection()
    if not conn:
        return []
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, location_name, alert_type, `condition`, threshold, metric_type, is_active, notify_method, description,
                   alert_mode, custom_config, cooldown_minutes, is_triggered, last_trigger_message, last_evaluated,
                   last_triggered, created_at, updated_at
            FROM weather_alerts
            ORDER BY id DESC
            """
        )
        rows = cur.fetchall()
        alerts = []
        for r in rows:
            alerts.append({
                'id': r[0],
                'location_name': r[1],
                'alert_type': r[2],
                'condition': r[3],
                'threshold': float(r[4]) if r[4] is not None else None,
                'metric_type': r[5],
                'is_active': bool(r[6]),
                'notify_method': r[7],
                'description': r[8],
                'alert_mode': r[9] or "standard",
                'custom_config': _safe_json_loads(r[10], {}),
                'cooldown_minutes': int(r[11]) if r[11] is not None else 15,
                'is_triggered': bool(r[12]),
                'last_trigger_message': r[13],
                'last_evaluated': _to_iso(r[14]),
                'last_triggered': _to_iso(r[15]),
                'created_at': _to_iso(r[16]),
                'updated_at': _to_iso(r[17]),
            })
        return alerts
    except Exception as e:
        print(f"Error fetching weather alerts: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def delete_weather_alert(alert_id):
    conn = create_connection()
    if not conn:
        return False
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM weather_alerts WHERE id = %s", (alert_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting weather alert: {e}")
        return False
    finally:
        cur.close()
        conn.close()

# ==================== SOCIAL MEDIA TREND ALERTS ====================

def create_social_trend_alerts_table():
    conn = create_connection()
    if not conn:
        print('Failed to create social trend alerts table: DB connection failed')
        return
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS social_trend_alerts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            trend_name VARCHAR(255) NOT NULL,
            source_platform VARCHAR(50) NOT NULL,
            alert_type VARCHAR(50) NOT NULL,
            `condition` ENUM('gt','lt','eq') NOT NULL,
            threshold INT NOT NULL,
            metric_type VARCHAR(50) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            notify_method VARCHAR(50) DEFAULT 'console',
            description TEXT,
            alert_mode VARCHAR(20) DEFAULT 'standard',
            custom_config TEXT NULL,
            cooldown_minutes INT DEFAULT 15,
            is_triggered BOOLEAN DEFAULT FALSE,
            last_trigger_message TEXT NULL,
            last_evaluated TIMESTAMP NULL,
            last_triggered TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_trend (trend_name),
            INDEX idx_platform (source_platform),
            INDEX idx_active (is_active),
            INDEX idx_metric (metric_type)
        )
    """)
    for stmt in [
        "ALTER TABLE social_trend_alerts ADD COLUMN alert_mode VARCHAR(20) DEFAULT 'standard'",
        "ALTER TABLE social_trend_alerts ADD COLUMN custom_config TEXT NULL",
        "ALTER TABLE social_trend_alerts ADD COLUMN cooldown_minutes INT DEFAULT 15",
        "ALTER TABLE social_trend_alerts ADD COLUMN is_triggered BOOLEAN DEFAULT FALSE",
        "ALTER TABLE social_trend_alerts ADD COLUMN last_trigger_message TEXT NULL",
        "ALTER TABLE social_trend_alerts ADD COLUMN last_evaluated TIMESTAMP NULL",
    ]:
        try:
            cur.execute(stmt)
        except Exception:
            pass

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS social_trend_alert_events (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            alert_id INT NOT NULL,
            trend_name VARCHAR(255) NOT NULL,
            source_platform VARCHAR(50) NOT NULL,
            event_type VARCHAR(30) NOT NULL,
            message TEXT,
            metric_type VARCHAR(50),
            metric_value DECIMAL(20,6) NULL,
            payload_json TEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_alert_id (alert_id),
            INDEX idx_trend (trend_name),
            INDEX idx_platform (source_platform),
            INDEX idx_event_type (event_type),
            INDEX idx_created_at (created_at)
        )
    """
    )
    conn.commit()
    cur.close()
    conn.close()
    print('social_trend_alerts table ensured')


def insert_social_trend_alert(
    trend_name,
    source_platform,
    alert_type,
    condition,
    threshold,
    metric_type,
    is_active=True,
    notify_method='console',
    description=None,
    alert_mode="standard",
    custom_config=None,
    cooldown_minutes=15,
):
    conn = create_connection()
    if not conn:
        return False
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO social_trend_alerts
            (trend_name, source_platform, alert_type, `condition`, threshold, metric_type, is_active, notify_method, description, alert_mode, custom_config, cooldown_minutes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                trend_name,
                source_platform,
                alert_type,
                condition,
                threshold,
                metric_type,
                is_active,
                notify_method,
                description,
                alert_mode,
                json.dumps(custom_config or {}),
                cooldown_minutes,
            ),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error inserting social trend alert: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def _get_latest_weather_metric(location_name, metric_type):
    conn = create_connection()
    if not conn:
        return None
    cur = conn.cursor()
    try:
        column = {
            "temperature": "temperature",
            "humidity": "humidity",
            "wind_speed": "wind_speed",
            "pressure": "pressure",
            "feels_like": "feels_like",
            "cloudiness": "cloudiness",
            "visibility": "visibility",
        }.get(metric_type)
        if not column:
            return None
        cur.execute(
            f"SELECT {column}, last_updated FROM weather_latest WHERE location_name = %s LIMIT 1",
            (location_name,),
        )
        row = cur.fetchone()
        if not row or row[0] is None:
            return None
        return {"metric_value": float(row[0]), "timestamp": _to_iso(row[1])}
    except Exception:
        return None
    finally:
        cur.close()
        conn.close()


def _update_weather_alert_state(alert_id, is_triggered, message, triggered_now=False):
    conn = create_connection()
    if not conn:
        return False
    cur = conn.cursor()
    try:
        if triggered_now:
            cur.execute(
                """
                UPDATE weather_alerts
                SET is_triggered = %s,
                    last_trigger_message = %s,
                    last_evaluated = UTC_TIMESTAMP(),
                    last_triggered = UTC_TIMESTAMP()
                WHERE id = %s
                """,
                (is_triggered, message, alert_id),
            )
        else:
            cur.execute(
                """
                UPDATE weather_alerts
                SET is_triggered = %s,
                    last_trigger_message = %s,
                    last_evaluated = UTC_TIMESTAMP()
                WHERE id = %s
                """,
                (is_triggered, message, alert_id),
            )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        cur.close()
        conn.close()


def _insert_weather_alert_event(alert_id, location_name, event_type, message, metric_type, metric_value=None, payload=None):
    conn = create_connection()
    if not conn:
        return False
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO weather_alert_events
            (alert_id, location_name, event_type, message, metric_type, metric_value, payload_json)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            """,
            (alert_id, location_name, event_type, message, metric_type, metric_value, json.dumps(payload or {})),
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        cur.close()
        conn.close()


def evaluate_weather_alerts(trigger_source="scheduler", dispatch_notifications=True):
    alerts = [a for a in get_weather_alerts() if a.get("is_active")]
    evaluated = []

    for alert in alerts:
        latest = _get_latest_weather_metric(alert["location_name"], alert["metric_type"])
        if not latest:
            msg = "Metric unavailable"
            _update_weather_alert_state(alert["id"], False, msg, triggered_now=False)
            evaluated.append({**alert, "is_match": False, "current_metric_value": None, "state_message": msg})
            continue

        value = float(latest["metric_value"])
        threshold = float(alert["threshold"])
        is_match = _compare_value(alert["condition"], value, threshold)
        cooldown_minutes = int(alert.get("cooldown_minutes") or 15)
        in_cooldown = _within_cooldown(alert.get("last_triggered"), cooldown_minutes)
        state_message = f"{alert['metric_type']}={value:.4f} {alert['condition']} {threshold:.4f}"

        if is_match and not in_cooldown:
            notify_message = f"[WEATHER ALERT] {alert['location_name']}: {state_message}"
            sent_ok, sent_status = (True, "skipped")
            if dispatch_notifications:
                sent_ok, sent_status = send_alert_notification(
                    {"notify_method": alert.get("notify_method"), "symbol": alert.get("location_name")},
                    notify_message,
                    module_key="weather",
                )
            _update_weather_alert_state(alert["id"], True, state_message, triggered_now=True)
            _insert_weather_alert_event(
                alert["id"], alert["location_name"], "triggered", f"{state_message} | notify={sent_status}",
                alert["metric_type"], value,
                payload={"trigger_source": trigger_source, "sent_ok": sent_ok},
            )
        elif is_match and in_cooldown:
            msg = f"{state_message} | in cooldown ({cooldown_minutes}m)"
            _update_weather_alert_state(alert["id"], True, msg, triggered_now=False)
            _insert_weather_alert_event(
                alert["id"], alert["location_name"], "cooldown", msg, alert["metric_type"], value,
                payload={"trigger_source": trigger_source},
            )
        else:
            was_triggered = bool(alert.get("is_triggered"))
            _update_weather_alert_state(alert["id"], False, state_message, triggered_now=False)
            if was_triggered:
                _insert_weather_alert_event(
                    alert["id"], alert["location_name"], "resolved", state_message, alert["metric_type"], value,
                    payload={"trigger_source": trigger_source},
                )

        evaluated.append({**alert, "is_match": is_match, "in_cooldown": in_cooldown, "current_metric_value": value, "state_message": state_message})
    return evaluated


def get_social_trend_alerts():
    conn = create_connection()
    if not conn:
        return []
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, trend_name, source_platform, alert_type, `condition`, threshold, metric_type, is_active, notify_method, description,
                   alert_mode, custom_config, cooldown_minutes, is_triggered, last_trigger_message, last_evaluated,
                   last_triggered, created_at, updated_at
            FROM social_trend_alerts
            ORDER BY id DESC
            """
        )
        rows = cur.fetchall()
        alerts = []
        for r in rows:
            alerts.append({
                'id': r[0],
                'trend_name': r[1],
                'source_platform': r[2],
                'alert_type': r[3],
                'condition': r[4],
                'threshold': int(r[5]) if r[5] is not None else None,
                'metric_type': r[6],
                'is_active': bool(r[7]),
                'notify_method': r[8],
                'description': r[9],
                'alert_mode': r[10] or "standard",
                'custom_config': _safe_json_loads(r[11], {}),
                'cooldown_minutes': int(r[12]) if r[12] is not None else 15,
                'is_triggered': bool(r[13]),
                'last_trigger_message': r[14],
                'last_evaluated': _to_iso(r[15]),
                'last_triggered': _to_iso(r[16]),
                'created_at': _to_iso(r[17]),
                'updated_at': _to_iso(r[18]),
            })
        return alerts
    except Exception as e:
        print(f"Error fetching social trend alerts: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def delete_social_trend_alert(alert_id):
    conn = create_connection()
    if not conn:
        return False
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM social_trend_alerts WHERE id = %s", (alert_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting social trend alert: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def _get_latest_social_metric(trend_name, source_platform, metric_type):
    conn = create_connection()
    if not conn:
        return None
    cur = conn.cursor()
    try:
        column = {
            "volume": "volume",
            "engagement": "engagement_count",
            "rank": "rank_position",
        }.get(metric_type)
        if not column:
            return None
        cur.execute(
            f"""
            SELECT trend_name, {column}, data_collected_at
            FROM social_latest
            WHERE source_platform = %s AND LOWER(trend_name) LIKE LOWER(%s)
            ORDER BY data_collected_at DESC
            LIMIT 1
            """,
            (source_platform, f"%{trend_name}%"),
        )
        row = cur.fetchone()
        if not row or row[1] is None:
            return None
        return {"matched_trend_name": row[0], "metric_value": float(row[1]), "timestamp": _to_iso(row[2])}
    except Exception:
        return None
    finally:
        cur.close()
        conn.close()


def _update_social_alert_state(alert_id, is_triggered, message, triggered_now=False):
    conn = create_connection()
    if not conn:
        return False
    cur = conn.cursor()
    try:
        if triggered_now:
            cur.execute(
                """
                UPDATE social_trend_alerts
                SET is_triggered = %s,
                    last_trigger_message = %s,
                    last_evaluated = UTC_TIMESTAMP(),
                    last_triggered = UTC_TIMESTAMP()
                WHERE id = %s
                """,
                (is_triggered, message, alert_id),
            )
        else:
            cur.execute(
                """
                UPDATE social_trend_alerts
                SET is_triggered = %s,
                    last_trigger_message = %s,
                    last_evaluated = UTC_TIMESTAMP()
                WHERE id = %s
                """,
                (is_triggered, message, alert_id),
            )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        cur.close()
        conn.close()


def _insert_social_alert_event(alert_id, trend_name, source_platform, event_type, message, metric_type, metric_value=None, payload=None):
    conn = create_connection()
    if not conn:
        return False
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO social_trend_alert_events
            (alert_id, trend_name, source_platform, event_type, message, metric_type, metric_value, payload_json)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (alert_id, trend_name, source_platform, event_type, message, metric_type, metric_value, json.dumps(payload or {})),
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        cur.close()
        conn.close()


def evaluate_social_trend_alerts(trigger_source="scheduler", dispatch_notifications=True):
    alerts = [a for a in get_social_trend_alerts() if a.get("is_active")]
    evaluated = []

    for alert in alerts:
        latest = _get_latest_social_metric(alert["trend_name"], alert["source_platform"], alert["metric_type"])
        if not latest:
            msg = "Metric unavailable"
            _update_social_alert_state(alert["id"], False, msg, triggered_now=False)
            evaluated.append({**alert, "is_match": False, "current_metric_value": None, "state_message": msg})
            continue

        value = float(latest["metric_value"])
        threshold = float(alert["threshold"])
        is_match = _compare_value(alert["condition"], value, threshold)
        cooldown_minutes = int(alert.get("cooldown_minutes") or 15)
        in_cooldown = _within_cooldown(alert.get("last_triggered"), cooldown_minutes)
        state_message = f"{alert['metric_type']}={value:.4f} {alert['condition']} {threshold:.4f} (matched={latest['matched_trend_name']})"

        if is_match and not in_cooldown:
            notify_message = f"[SOCIAL ALERT] {alert['source_platform']}:{alert['trend_name']} {state_message}"
            sent_ok, sent_status = (True, "skipped")
            if dispatch_notifications:
                sent_ok, sent_status = send_alert_notification(
                    {"notify_method": alert.get("notify_method"), "symbol": f"{alert.get('source_platform')}:{alert.get('trend_name')}"},
                    notify_message,
                    module_key="social",
                )
            _update_social_alert_state(alert["id"], True, state_message, triggered_now=True)
            _insert_social_alert_event(
                alert["id"], alert["trend_name"], alert["source_platform"], "triggered",
                f"{state_message} | notify={sent_status}", alert["metric_type"], value,
                payload={"trigger_source": trigger_source, "sent_ok": sent_ok},
            )
        elif is_match and in_cooldown:
            msg = f"{state_message} | in cooldown ({cooldown_minutes}m)"
            _update_social_alert_state(alert["id"], True, msg, triggered_now=False)
            _insert_social_alert_event(
                alert["id"], alert["trend_name"], alert["source_platform"], "cooldown",
                msg, alert["metric_type"], value, payload={"trigger_source": trigger_source},
            )
        else:
            was_triggered = bool(alert.get("is_triggered"))
            _update_social_alert_state(alert["id"], False, state_message, triggered_now=False)
            if was_triggered:
                _insert_social_alert_event(
                    alert["id"], alert["trend_name"], alert["source_platform"], "resolved",
                    state_message, alert["metric_type"], value, payload={"trigger_source": trigger_source},
                )

        evaluated.append({**alert, "is_match": is_match, "in_cooldown": in_cooldown, "current_metric_value": value, "state_message": state_message})
    return evaluated
