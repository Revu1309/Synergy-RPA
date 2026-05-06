"""Database-backed user/module/page access control."""

import hashlib
from typing import Dict, List, Optional
from .connection import create_connection, get_cursor, is_postgres

def hash_password(password: str) -> str:
    return hashlib.sha256((password or "").encode()).hexdigest()

def create_access_control_tables() -> None:
    conn = create_connection()
    if not conn:
        return
    cur = get_cursor(conn)
    try:
        if is_postgres(conn):
            # Postgres Schema
            cur.execute("""
                CREATE TABLE IF NOT EXISTS app_users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    is_admin BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_users_un ON app_users(username)")
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS app_modules (
                    id SERIAL PRIMARY KEY,
                    module_key VARCHAR(100) NOT NULL UNIQUE,
                    module_name VARCHAR(120) NOT NULL,
                    module_description VARCHAR(255),
                    display_order INT DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS app_pages (
                    id SERIAL PRIMARY KEY,
                    page_key VARCHAR(120) NOT NULL UNIQUE,
                    module_key VARCHAR(100) NOT NULL,
                    page_name VARCHAR(150) NOT NULL,
                    route_path VARCHAR(200) NOT NULL UNIQUE,
                    menu_label VARCHAR(150),
                    page_description VARCHAR(255),
                    display_order INT DEFAULT 0,
                    is_menu_visible BOOLEAN DEFAULT TRUE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (module_key) REFERENCES app_modules(module_key) ON DELETE CASCADE
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_page_permissions (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) NOT NULL,
                    page_key VARCHAR(120) NOT NULL,
                    is_allowed BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (username, page_key),
                    FOREIGN KEY (username) REFERENCES app_users(username) ON DELETE CASCADE,
                    FOREIGN KEY (page_key) REFERENCES app_pages(page_key) ON DELETE CASCADE
                )
            """)
        else:
            # MySQL Schema
            cur.execute("""
                CREATE TABLE IF NOT EXISTS app_users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    is_admin BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_username (username),
                    INDEX idx_active (is_active)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS app_modules (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    module_key VARCHAR(100) NOT NULL UNIQUE,
                    module_name VARCHAR(120) NOT NULL,
                    module_description VARCHAR(255),
                    display_order INT DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_module_key (module_key)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS app_pages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    page_key VARCHAR(120) NOT NULL UNIQUE,
                    module_key VARCHAR(100) NOT NULL,
                    page_name VARCHAR(150) NOT NULL,
                    route_path VARCHAR(200) NOT NULL UNIQUE,
                    menu_label VARCHAR(150),
                    page_description VARCHAR(255),
                    display_order INT DEFAULT 0,
                    is_menu_visible BOOLEAN DEFAULT TRUE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_module_key (module_key),
                    FOREIGN KEY (module_key) REFERENCES app_modules(module_key) ON DELETE CASCADE
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_page_permissions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) NOT NULL,
                    page_key VARCHAR(120) NOT NULL,
                    is_allowed BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_user_page (username, page_key),
                    FOREIGN KEY (username) REFERENCES app_users(username) ON DELETE CASCADE,
                    FOREIGN KEY (page_key) REFERENCES app_pages(page_key) ON DELETE CASCADE
                )
            """)
        conn.commit()
    finally:
        cur.close()
        conn.close()

def seed_default_access_config() -> None:
    conn = create_connection()
    if not conn:
        return
    cur = get_cursor(conn)
    try:
        modules = [
            ("crypto", "Crypto", "Cryptocurrency analytics and alerts", 10),
            ("weather", "Weather", "Weather dashboards and locations", 20),
            ("social", "Social", "Social trends and alerts", 30),
            ("monitoring", "Monitoring", "Pipeline freshness and operational status", 35),
            ("admin", "Administration", "User/module/page management", 40),
        ]
        for module in modules:
            if is_postgres(conn):
                query = """
                INSERT INTO app_modules (module_key, module_name, module_description, display_order)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (module_key) DO UPDATE SET
                    module_name = EXCLUDED.module_name,
                    module_description = EXCLUDED.module_description,
                    display_order = EXCLUDED.display_order
                """
            else:
                query = """
                INSERT INTO app_modules (module_key, module_name, module_description, display_order)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    module_name = VALUES(module_name),
                    module_description = VALUES(module_description),
                    display_order = VALUES(display_order)
                """
            cur.execute(query, module)

        pages = [
            ("crypto_standard_dashboard", "crypto", "Standard Dashboard", "/asset-dashboard", "Standard Dashboard", "Interactive crypto analytics", 10, True),
            ("crypto_advanced_dashboard", "crypto", "Advanced Analytics", "/advanced-crypto-dashboard", "Advanced Analytics", "Deep crypto analytics", 20, True),
            ("crypto_asset_management", "crypto", "Manage Assets", "/asset-management", "Manage Assets", "Manage tracked assets", 30, True),
            ("crypto_alerts", "crypto", "Price Alerts", "/crypto-alerts", "Price Alerts", "Create and manage crypto alerts", 40, True),
            ("weather_dashboard", "weather", "Weather Dashboard", "/weather-dashboard", "Weather Dashboard", "Weather data dashboard", 10, True),
            ("weather_advanced_dashboard", "weather", "Advanced Weather Analytics", "/advanced-weather-dashboard", "Advanced Analytics", "Advanced weather analytics", 20, True),
            ("weather_locations", "weather", "Manage Locations", "/manage-locations", "Manage Locations", "Manage weather locations", 30, True),
            ("weather_alerts", "weather", "Weather Alerts", "/weather-alerts", "Weather Alerts", "Weather alert rules", 40, True),
            ("social_dashboard", "social", "Trends Dashboard", "/social-trends-dashboard", "Trends Dashboard", "Social trends overview", 10, True),
            ("social_advanced_dashboard", "social", "Advanced Trends Analytics", "/advanced-social-trends-dashboard", "Advanced Analytics", "Advanced social insights", 20, True),
            ("social_alerts", "social", "Trend Alerts", "/social-trend-alerts", "Trend Alerts", "Social trend alerts", 30, True),
            ("data_freshness_monitor", "monitoring", "Data Freshness Monitor", "/data-freshness-monitor", "Data Freshness Monitor", "Show last successful sync and stale pipelines", 10, True),
            ("signal_fusion_report", "monitoring", "Signal Fusion Report", "/signal-fusion-report", "Signal Fusion Report", "Fused crypto/social/weather score report", 20, True),
            ("admin_user_management", "admin", "User Management", "/admin/users", "User Management", "Create and manage users", 5, True),
            ("admin_access_control", "admin", "Access Control", "/admin/access-control", "Access Control", "Assign module/page permissions", 10, True),
            ("admin_alert_settings", "admin", "Alert Settings", "/admin/alert-settings", "Alert Settings", "Manage alert messaging channels by module", 15, True),
        ]
        for page in pages:
            if is_postgres(conn):
                query = """
                INSERT INTO app_pages
                    (page_key, module_key, page_name, route_path, menu_label, page_description, display_order, is_menu_visible)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (page_key) DO UPDATE SET
                    module_key = EXCLUDED.module_key,
                    page_name = EXCLUDED.page_name,
                    route_path = EXCLUDED.route_path,
                    menu_label = EXCLUDED.menu_label,
                    page_description = EXCLUDED.page_description,
                    display_order = EXCLUDED.display_order,
                    is_menu_visible = EXCLUDED.is_menu_visible
                """
            else:
                query = """
                INSERT INTO app_pages
                    (page_key, module_key, page_name, route_path, menu_label, page_description, display_order, is_menu_visible)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    module_key = VALUES(module_key),
                    page_name = VALUES(page_name),
                    route_path = VALUES(route_path),
                    menu_label = VALUES(menu_label),
                    page_description = VALUES(page_description),
                    display_order = VALUES(display_order),
                    is_menu_visible = VALUES(is_menu_visible)
                """
            cur.execute(query, page)

        cur.execute("SELECT id FROM app_users WHERE username = %s", ("admin",))
        if not cur.fetchone():
            cur.execute(
                """
                INSERT INTO app_users (username, password_hash, is_admin, is_active)
                VALUES (%s, %s, %s, %s)
                """,
                ("admin", hash_password("admin"), True, True),
            )

        cur.execute("SELECT page_key FROM app_pages WHERE is_active = TRUE")
        all_pages = [row[0] for row in cur.fetchall()]
        for page_key in all_pages:
            if is_postgres(conn):
                query = """
                INSERT INTO user_page_permissions (username, page_key, is_allowed)
                VALUES (%s, %s, TRUE)
                ON CONFLICT (username, page_key) DO UPDATE SET is_allowed = TRUE
                """
            else:
                query = """
                INSERT INTO user_page_permissions (username, page_key, is_allowed)
                VALUES (%s, %s, TRUE)
                ON DUPLICATE KEY UPDATE is_allowed = TRUE
                """
            cur.execute(query, ("admin", page_key))

        conn.commit()
    finally:
        cur.close()
        conn.close()

def verify_user_credentials(username: str, password: str) -> bool:
    conn = create_connection()
    if not conn: return False
    cur = get_cursor(conn)
    try:
        cur.execute("SELECT password_hash, is_active FROM app_users WHERE username = %s", (username,))
        row = cur.fetchone()
        if not row: return False
        return bool(row[1]) and row[0] == hash_password(password)
    finally:
        cur.close()
        conn.close()

def is_admin_user(username: str) -> bool:
    conn = create_connection()
    if not conn: return username == "admin"
    cur = get_cursor(conn)
    try:
        cur.execute("SELECT is_admin FROM app_users WHERE username = %s AND is_active = TRUE", (username,))
        row = cur.fetchone()
        return bool(row and row[0])
    finally:
        cur.close()
        conn.close()

def list_users() -> List[Dict]:
    conn = create_connection()
    if not conn: return []
    cur = get_cursor(conn, dictionary=True)
    try:
        cur.execute("SELECT username, is_admin, is_active, created_at, updated_at FROM app_users ORDER BY username ASC")
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def create_user(username: str, password: str, is_admin: bool = False, is_active: bool = True) -> bool:
    conn = create_connection()
    if not conn: return False
    cur = get_cursor(conn)
    try:
        cur.execute(
            "INSERT INTO app_users (username, password_hash, is_admin, is_active) VALUES (%s, %s, %s, %s)",
            (username, hash_password(password), bool(is_admin), bool(is_active)),
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        cur.close()
        conn.close()

def update_user(username: str, is_admin: Optional[bool] = None, is_active: Optional[bool] = None) -> bool:
    conn = create_connection()
    if not conn: return False
    cur = get_cursor(conn)
    try:
        fields = []
        values = []
        if is_admin is not None:
            fields.append("is_admin = %s")
            values.append(bool(is_admin))
        if is_active is not None:
            fields.append("is_active = %s")
            values.append(bool(is_active))
        if not fields: return True
        values.append(username)
        cur.execute(f"UPDATE app_users SET {', '.join(fields)} WHERE username = %s", tuple(values))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        cur.close()
        conn.close()

def reset_user_password(username: str, password: str) -> bool:
    conn = create_connection()
    if not conn: return False
    cur = get_cursor(conn)
    try:
        cur.execute("UPDATE app_users SET password_hash = %s WHERE username = %s", (hash_password(password), username))
        conn.commit()
        return cur.rowcount > 0
    except Exception:
        return False
    finally:
        cur.close()
        conn.close()

def get_modules_with_pages() -> List[Dict]:
    conn = create_connection()
    if not conn: return []
    cur = get_cursor(conn, dictionary=True)
    try:
        cur.execute("""
            SELECT m.module_key, m.module_name, m.module_description, m.display_order AS module_order,
                   p.page_key, p.page_name, p.route_path, p.menu_label, p.page_description, 
                   p.display_order AS page_order, p.is_menu_visible
            FROM app_modules m
            JOIN app_pages p ON p.module_key = m.module_key
            WHERE m.is_active = TRUE AND p.is_active = TRUE
            ORDER BY m.display_order ASC, p.display_order ASC
        """)
        rows = cur.fetchall()
        modules: Dict[str, Dict] = {}
        for row in rows:
            m_key = row["module_key"]
            if m_key not in modules:
                modules[m_key] = {
                    "module_key": m_key,
                    "module_name": row["module_name"],
                    "module_description": row["module_description"],
                    "display_order": row["module_order"],
                    "pages": [],
                }
            modules[m_key]["pages"].append({
                "page_key": row["page_key"],
                "page_name": row["page_name"],
                "route_path": row["route_path"],
                "menu_label": row["menu_label"] or row["page_name"],
                "page_description": row["page_description"] or "",
                "display_order": row["page_order"],
                "is_menu_visible": bool(row["is_menu_visible"]),
            })
        return list(modules.values())
    finally:
        cur.close()
        conn.close()

def get_user_allowed_page_keys(username: str) -> List[str]:
    conn = create_connection()
    if not conn: return []
    cur = get_cursor(conn)
    try:
        cur.execute("""
            SELECT upp.page_key
            FROM user_page_permissions upp
            JOIN app_pages p ON p.page_key = upp.page_key
            WHERE upp.username = %s AND upp.is_allowed = TRUE AND p.is_active = TRUE
        """, (username,))
        return [row[0] for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

def set_user_allowed_pages(username: str, allowed_page_keys: List[str]) -> bool:
    conn = create_connection()
    if not conn: return False
    cur = get_cursor(conn)
    try:
        cur.execute("SELECT page_key FROM app_pages WHERE is_active = TRUE")
        all_page_keys = [row[0] for row in cur.fetchall()]
        allowed_set = set(allowed_page_keys or [])
        for page_key in all_page_keys:
            is_allowed = page_key in allowed_set
            if is_postgres(conn):
                query = """
                INSERT INTO user_page_permissions (username, page_key, is_allowed)
                VALUES (%s, %s, %s)
                ON CONFLICT (username, page_key) DO UPDATE SET is_allowed = EXCLUDED.is_allowed
                """
            else:
                query = """
                INSERT INTO user_page_permissions (username, page_key, is_allowed)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE is_allowed = VALUES(is_allowed)
                """
            cur.execute(query, (username, page_key, is_allowed))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        cur.close()
        conn.close()

def get_user_menu_modules(username: str) -> List[Dict]:
    modules = get_modules_with_pages()
    allowed = set(get_user_allowed_page_keys(username))
    result = []
    for mod in modules:
        pages = [p for p in mod["pages"] if p["is_menu_visible"] and p["page_key"] in allowed]
        if pages:
            result.append({
                "module_key": mod["module_key"],
                "module_name": mod["module_name"],
                "module_description": mod["module_description"] or "",
                "display_order": mod["display_order"],
                "pages": pages,
            })
    return result

def get_first_allowed_route(username: str) -> str:
    conn = create_connection()
    if not conn: return "/menu"
    cur = get_cursor(conn)
    try:
        cur.execute("""
            SELECT p.route_path
            FROM user_page_permissions upp
            JOIN app_pages p ON p.page_key = upp.page_key
            JOIN app_modules m ON m.module_key = p.module_key
            WHERE upp.username = %s AND upp.is_allowed = TRUE AND p.is_active = TRUE AND m.is_active = TRUE
            ORDER BY m.display_order ASC, p.display_order ASC
            LIMIT 1
        """, (username,))
        row = cur.fetchone()
        return row[0] if row and row[0] else "/menu"
    finally:
        cur.close()
        conn.close()

def normalize_path(path: str) -> str:
    if not path: return "/"
    cleaned = path.split("?", 1)[0].strip()
    if cleaned != "/" and cleaned.endswith("/"): cleaned = cleaned[:-1]
    return cleaned or "/"

def user_can_access_path(username: str, path: str) -> bool:
    normalized = normalize_path(path)
    conn = create_connection()
    if not conn: return username == "admin"
    cur = get_cursor(conn)
    try:
        cur.execute("SELECT page_key FROM app_pages WHERE route_path = %s AND is_active = TRUE", (normalized,))
        row = cur.fetchone()
        if not row: return True
        page_key = row[0]
        cur.execute("SELECT is_allowed FROM user_page_permissions WHERE username = %s AND page_key = %s", (username, page_key))
        perm = cur.fetchone()
        return bool(perm and perm[0])
    finally:
        cur.close()
        conn.close()
