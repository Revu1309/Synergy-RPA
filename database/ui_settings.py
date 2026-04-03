import json

from .connection import create_connection


DEFAULT_THEME = "ocean"


def create_ui_settings_table():
    conn = create_connection()
    if not conn:
        return
    cur = conn.cursor()
    try:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS ui_theme_settings (
                username VARCHAR(100) PRIMARY KEY,
                theme_key VARCHAR(30) NOT NULL DEFAULT 'ocean',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES app_users(username) ON DELETE CASCADE
            )
            """
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()


def get_user_theme(username):
    if not username:
        return DEFAULT_THEME
    conn = create_connection()
    if not conn:
        return DEFAULT_THEME
    cur = conn.cursor()
    try:
        cur.execute("SELECT theme_key FROM ui_theme_settings WHERE username = %s", (username,))
        row = cur.fetchone()
        if not row or not row[0]:
            return DEFAULT_THEME
        return row[0]
    finally:
        cur.close()
        conn.close()


def set_user_theme(username, theme_key):
    if not username:
        return False
    conn = create_connection()
    if not conn:
        return False
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO ui_theme_settings (username, theme_key)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE theme_key = VALUES(theme_key), updated_at = CURRENT_TIMESTAMP
            """,
            (username, theme_key),
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        cur.close()
        conn.close()
