"""Database models for user preferences and landing page settings."""

from .connection import create_connection
from datetime import datetime


def create_user_preferences_table():
    """Create the user_preferences table to store user landing page settings."""
    conn = create_connection()
    if not conn:
        print('Failed to create user_preferences table: DB connection failed')
        return
    cur = conn.cursor()
    try:
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
    """Get the landing page for a specific user.
    
    Args:
        username: The username to look up
        
    Returns:
        str: The landing page URL (default: '/menu-v2' for admin, '/menu' for others)
    """
    conn = create_connection()
    if not conn:
        # Default for admin is /menu-v2
        return '/menu-v2' if username == 'admin' else '/menu'
    
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT landing_page FROM user_preferences WHERE username = %s AND is_active = TRUE",
            (username,)
        )
        result = cur.fetchone()
        
        if result and result[0]:
            landing_page = result[0]
        else:
            # Default based on role/username
            landing_page = '/menu-v2' if username == 'admin' else '/menu'
        
        return landing_page
    except Exception as e:
        print(f"Error getting user landing page for {username}: {e}")
        return '/menu-v2' if username == 'admin' else '/menu'
    finally:
        cur.close()
        conn.close()


def get_user_role(username):
    """Get the user role.
    
    Args:
        username: The username to look up
        
    Returns:
        str: The user role (default: 'admin')
    """
    conn = create_connection()
    if not conn:
        return 'admin' if username == 'admin' else 'user'
    
    cur = conn.cursor()
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
    """Set the landing page for a user.
    
    Args:
        username: The username
        landing_page: The landing page URL (e.g., '/menu-v2', '/menu')
        user_role: The user role (e.g., 'admin', 'analyst', 'monitor')
        
    Returns:
        bool: True if successful, False otherwise
    """
    conn = create_connection()
    if not conn:
        return False
    
    cur = conn.cursor()
    try:
        # Check if user exists
        cur.execute("SELECT id FROM user_preferences WHERE username = %s", (username,))
        exists = cur.fetchone()
        
        if exists:
            # Update existing
            cur.execute(
                "UPDATE user_preferences SET landing_page = %s, user_role = %s WHERE username = %s",
                (landing_page, user_role, username)
            )
        else:
            # Insert new
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
    
    cur = conn.cursor()
    try:
        # Check if admin user exists in preferences
        cur.execute("SELECT id FROM user_preferences WHERE username = %s", ('admin',))
        if not cur.fetchone():
            # Admin goes to menu-v2
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
