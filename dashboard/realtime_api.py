"""
Real-time API endpoints for live data streaming.
Integrates with the dashboard to provide Server-Sent Events (SSE) for live updates.
"""

import logging
import json
from datetime import datetime, timezone
from functools import wraps
from typing import Dict, Iterator, Optional

logger = logging.getLogger(__name__)


def sse_event(event_type: str, data: Dict) -> str:
    """
    Format data as Server-Sent Event.
    
    Args:
        event_type: Event type (e.g., 'crypto-update', 'weather-update')
        data: Event data dict
        
    Returns:
        SSE formatted string
    """
    try:
        json_data = json.dumps(data, default=str)
        return f"event: {event_type}\ndata: {json_data}\n\n"
    except Exception as e:
        logger.error(f"Error formatting SSE event: {e}")
        return f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"


def create_realtime_endpoints(app, cache, db_connection):
    """
    Create real-time API endpoints for the Flask app.
    
    Args:
        app: Flask application
        cache: RealtimeDataCache instance
        db_connection: Database connection function or module
    """
    
    @app.route('/api/realtime/crypto-stream')
    def crypto_stream():
        """Server-Sent Events stream for crypto updates."""
        def generate():
            try:
                # Send initial data
                crypto_data = cache.get_crypto()
                yield sse_event('crypto-update', {
                    'assets': crypto_data,
                    'count': len(crypto_data),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
                
                # In production, use Flask-SSE or similar for true streaming
                yield "event: connected\ndata: {\"message\": \"Stream connected\"}\n\n"
                
            except Exception as e:
                logger.error(f"Error in crypto stream: {e}")
                yield sse_event('error', {'error': str(e)})
        
        return app.response_class(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )
    
    @app.route('/api/realtime/weather-stream')
    def weather_stream():
        """Server-Sent Events stream for weather updates."""
        def generate():
            try:
                # Send initial data
                weather_data = cache.get_weather()
                yield sse_event('weather-update', {
                    'locations': weather_data,
                    'count': len(weather_data),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
                
                yield "event: connected\ndata: {\"message\": \"Stream connected\"}\n\n"
                
            except Exception as e:
                logger.error(f"Error in weather stream: {e}")
                yield sse_event('error', {'error': str(e)})
        
        return app.response_class(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )
    
    @app.route('/api/realtime/social-stream')
    def social_stream():
        """Server-Sent Events stream for social trends updates."""
        def generate():
            try:
                # Send initial data
                trends_data = cache.get_social_trends()
                yield sse_event('social-update', {
                    'trends': trends_data,
                    'count': len(trends_data),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
                
                yield "event: connected\ndata: {\"message\": \"Stream connected\"}\n\n"
                
            except Exception as e:
                logger.error(f"Error in social stream: {e}")
                yield sse_event('error', {'error': str(e)})
        
        return app.response_class(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )
    
    @app.route('/api/realtime/data')
    def get_all_realtime_data():
        """Get all current real-time data (JSON snapshot)."""
        try:
            return {
                'success': True,
                'data': {
                    'crypto': cache.get_crypto(),
                    'weather': cache.get_weather(),
                    'social_trends': cache.get_social_trends(),
                    'signal_fusion': cache.get_signal_fusion(),
                    'job_status': cache.get_job_status(),
                },
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stats': cache.get_all_stats()
            }
        except Exception as e:
            logger.error(f"Error in get_all_realtime_data: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }, 500
    
    @app.route('/api/realtime/crypto')
    def get_crypto_data():
        """Get current crypto data (JSON)."""
        try:
            symbol = request.args.get('symbol')
            data = cache.get_crypto(symbol) if symbol else cache.get_crypto()
            return {
                'success': True,
                'data': data,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Error in get_crypto_data: {e}")
            return {'success': False, 'error': str(e)}, 500
    
    @app.route('/api/realtime/weather')
    def get_weather_data():
        """Get current weather data (JSON)."""
        try:
            location = request.args.get('location')
            data = cache.get_weather(location) if location else cache.get_weather()
            return {
                'success': True,
                'data': data,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Error in get_weather_data: {e}")
            return {'success': False, 'error': str(e)}, 500
    
    @app.route('/api/realtime/social')
    def get_social_data():
        """Get current social trends data (JSON)."""
        try:
            data = cache.get_social_trends()
            return {
                'success': True,
                'data': data,
                'count': len(data),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Error in get_social_data: {e}")
            return {'success': False, 'error': str(e)}, 500
    
    @app.route('/api/realtime/signal-fusion')
    def get_signal_fusion():
        """Get current signal fusion index (JSON)."""
        try:
            data = cache.get_signal_fusion()
            return {
                'success': True,
                'data': data,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Error in get_signal_fusion: {e}")
            return {'success': False, 'error': str(e)}, 500
    
    @app.route('/api/realtime/job-status')
    def get_job_status_data():
        """Get job status data (JSON)."""
        try:
            job_id = request.args.get('job_id')
            data = cache.get_job_status(job_id) if job_id else cache.get_job_status()
            return {
                'success': True,
                'data': data,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Error in get_job_status_data: {e}")
            return {'success': False, 'error': str(e)}, 500
    
    @app.route('/api/realtime/stats')
    def get_cache_stats():
        """Get cache statistics for monitoring."""
        try:
            stats = cache.get_all_stats()
            return {
                'success': True,
                'data': stats,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Error in get_cache_stats: {e}")
            return {'success': False, 'error': str(e)}, 500
    
    logger.info("Real-time API endpoints registered successfully")
