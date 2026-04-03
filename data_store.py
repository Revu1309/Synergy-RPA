"""In-memory data store for latest snapshots of crypto, weather, and social data."""

from datetime import datetime

# Latest crypto snapshot
latest_crypto = []
latest_crypto_timestamp = None

# Latest weather snapshot
latest_weather = []
latest_weather_timestamp = None

# Latest social snapshot
latest_social = []
latest_social_timestamp = None


def set_crypto(data):
    """Set the latest crypto snapshot."""
    global latest_crypto, latest_crypto_timestamp
    latest_crypto = data
    latest_crypto_timestamp = datetime.utcnow()


def get_crypto():
    """Get the latest crypto snapshot."""
    return latest_crypto


def get_crypto_timestamp():
    """Get the timestamp of the latest crypto snapshot."""
    return latest_crypto_timestamp


def set_weather(data):
    """Set the latest weather snapshot."""
    global latest_weather, latest_weather_timestamp
    latest_weather = data
    latest_weather_timestamp = datetime.utcnow()


def get_weather():
    """Get the latest weather snapshot."""
    return latest_weather


def get_weather_timestamp():
    """Get the timestamp of the latest weather snapshot."""
    return latest_weather_timestamp


def set_social(data):
    """Set the latest social snapshot."""
    global latest_social, latest_social_timestamp
    latest_social = data
    latest_social_timestamp = datetime.utcnow()


def get_social():
    """Get the latest social snapshot."""
    return latest_social


def get_social_timestamp():
    """Get the timestamp of the latest social snapshot."""
    return latest_social_timestamp
