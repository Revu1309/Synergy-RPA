"""Database models for user preferences and landing page settings."""

from .connection import create_connection, get_cursor, is_postgres
from datetime import datetime


def create_user_preferences_table():
    """Create the user_preferences table to store user landing page settings."""
    conn = create_connection()
    if not conn:
        print('Failed to create user_preferences table: DB connection failed')
        return
    cur = get_cursor(conn)
    try:
        if is_postgres(conn):
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) NOT NULL UNIQUE,
                    landing_page VARCHAR(100) NOT NULL DEFAULT '/menu-v2',
                    user_role VARCHAR(50) DEFAULT 'admin',
                    theme VARCHAR(50) DEFAULT 'default',
                    language VARCHAR(20) DEFAULT 'en',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_up_username ON user_preferences(username)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_up_role ON user_preferences(user_role)")
        else:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) NOT NULL UNIQUE,
                    landing_page VARCHAR(100) NOT NULL DEFAULT '/menu-v2',
                    user_role VARCHAR(50) DEFAULT 'admin',
                    theme VARCHAR(50) DEFAULT 'default',
                    language VARCHAR(20) DEFAULT 'en',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_username (username),
                    INDEX idx_role (user_role)
                )
            """)
        conn.commit()
        print('✓ user_preferences table ensured')
    except Exception as e:
        print(f"Error creating user_preferences table: {e}")
    finally:
        cur.close()
        conn.close()


def get_user_landing_page(username):
    """Get the landing page for a specific user."""
    conn = create_connection()
    if not conn:
        return '/menu-v2' if username == 'admin' else '/menu'
    
    cur = get_cursor(conn)
    try:
        cur.execute(
            "SELECT landing_page FROM user_preferences WHERE username = %s AND is_active = TRUE",
            (username,)
        )
        result = cur.fetchone()
        
        if result and result[0]:
            landing_page = result[0]
        else:
            landing_page = '/menu-v2' if username == 'admin' else '/menu'
        
        return landing_page
    except Exception as e:
        # If table doesn't exist, return default instead of crashing
        print(f"Note: Could not fetch landing page (table may not exist yet): {e}")
        return '/menu-v2' if username == 'admin' else '/menu'
    finally:
        cur.close()
        conn.close()


def get_user_role(username):
    """Get the user role."""
    conn = create_connection()
    if not conn:
        return 'admin' if username == 'admin' else 'user'
    
    cur = get_cursor(conn)
    try:
        cur.execute(
            "SELECT user_role FROM user_preferences WHERE username = %s AND is_active = TRUE",
            (username,)
        )
        result = cur.fetchone()
        
        if result and result[0]:
            return result[0]
        else:
            return 'admin' if username == 'admin' else 'user'
    except Exception as e:
        print(f"Error getting user role for {username}: {e}")
        return 'admin' if username == 'admin' else 'user'
    finally:
        cur.close()
        conn.close()


def set_user_landing_page(username, landing_page, user_role='admin'):
    """Set the landing page for a user."""
    conn = create_connection()
    if not conn:
        return False
    
    cur = get_cursor(conn)
    try:
        if is_postgres(conn):
            query = """
            INSERT INTO user_preferences (username, landing_page, user_role)
            VALUES (%s, %s, %s)
            ON CONFLICT (username) DO UPDATE SET
                landing_page = EXCLUDED.landing_page,
                user_role = EXCLUDED.user_role,
                updated_at = CURRENT_TIMESTAMP
            """
            cur.execute(query, (username, landing_page, user_role))
        else:
            # Check if user exists for MySQL (standard fallback)
            cur.execute("SELECT id FROM user_preferences WHERE username = %s", (username,))
            exists = cur.fetchone()
            
            if exists:
                cur.execute(
                    "UPDATE user_preferences SET landing_page = %s, user_role = %s WHERE username = %s",
                    (landing_page, user_role, username)
                )
            else:
                cur.execute(
                    "INSERT INTO user_preferences (username, landing_page, user_role) VALUES (%s, %s, %s)",
                    (username, landing_page, user_role)
                )
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error setting user landing page for {username}: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def initialize_default_users():
    """Initialize default admin user preferences if not exists."""
    conn = create_connection()
    if not conn:
        return
    
    cur = get_cursor(conn)
    try:
        cur.execute("SELECT id FROM user_preferences WHERE username = %s", ('admin',))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO user_preferences (username, landing_page, user_role) VALUES (%s, %s, %s)",
                ('admin', '/menu-v2', 'admin')
            )
            conn.commit()
            print("✓ Initialized admin user preferences")
    except Exception as e:
        print(f"Error initializing default users: {e}")
    finally:
        cur.close()
        conn.close()
