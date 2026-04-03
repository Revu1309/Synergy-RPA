"""Authentication module for login functionality."""

import hashlib
from datetime import datetime, timedelta
import secrets
from database.access_control import verify_user_credentials

class AuthManager:
    """Manage user authentication."""
    
    # Default credentials
    USERS = {
        'admin': hashlib.sha256('admin'.encode()).hexdigest()
    }
    
    # Active sessions
    sessions = {}
    
    @staticmethod
    def hash_password(password):
        """Hash a password."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_credentials(username, password):
        """Verify if credentials are correct."""
        # Primary path: DB-backed users
        try:
            if verify_user_credentials(username, password):
                return True
        except Exception:
            pass

        # Fallback path for backward compatibility
        if username not in AuthManager.USERS:
            return False
        return AuthManager.USERS[username] == AuthManager.hash_password(password)
    
    @staticmethod
    def create_session(username):
        """Create a new session token."""
        token = secrets.token_urlsafe(32)
        AuthManager.sessions[token] = {
            'username': username,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(hours=24)
        }
        return token
    
    @staticmethod
    def verify_session(token):
        """Verify if session token is valid."""
        if token not in AuthManager.sessions:
            return False
        
        session = AuthManager.sessions[token]
        if datetime.now() > session['expires_at']:
            del AuthManager.sessions[token]
            return False
        return True
    
    @staticmethod
    def get_username(token):
        """Get username from session token."""
        if AuthManager.verify_session(token):
            return AuthManager.sessions[token]['username']
        return None
    
    @staticmethod
    def logout(token):
        """Logout a user."""
        if token in AuthManager.sessions:
            del AuthManager.sessions[token]
            return True
        return False
