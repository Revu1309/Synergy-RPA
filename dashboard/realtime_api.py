"""
Real-time API endpoints for live data streaming.
Integrates with the dashboard to provide Server-Sent Events (SSE) for live updates.
"""

import logging
import json
from datetime import datetime, timezone
from typing import Dict, Optional, Any
from flask import request

import queue
import threading

logger = logging.getLogger(__name__)


def sse_event(event_type: str, data: Dict) -> str:
    """Format a dict payload as an SSE event."""
    try:
        json_data = json.dumps(data, default=str)
        return f"event: {event_type}\ndata: {json_data}\n\n"
    except Exception as e:
        logger.error(f"Error formatting SSE event: {e}")
        return f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"


def _stream_from_cache(cache, subscribe_key: str, subscribe_fn, event_type: str, get_initial_payload_fn, to_client_fn):
    """Shared SSE streaming logic.

    - cache: RealtimeDataCache
    - subscribe_key: cache category string (e.g. 'crypto', 'weather')
    - subscribe_fn: function(payload) -> None passed to cache.subscribe
    - event_type: SSE event name
    - get_initial_payload_fn: () -> payload
    - to_client_fn: payload -> client payload (dict)
    """

    q: "queue.Queue[Any]" = queue.Queue()
    stop_event = threading.Event()

    def generate():
        try:
            # Initial snapshot
            initial_payload = get_initial_payload_fn()
            yield sse_event(event_type, to_client_fn(initial_payload))

            # Connection marker (helps frontend debug)
            yield "event: connected\ndata: {\"message\": \"Stream connected\"}\n\n"

            cache.subscribe(subscribe_key, subscribe_fn)
            try:
                while not stop_event.is_set():
                    payload = q.get()  # blocks until next update
                    yield sse_event(event_type, to_client_fn(payload))
            finally:
                cache.unsubscribe(subscribe_key, subscribe_fn)
        except Exception as e:
            logger.error(f"Error in SSE stream ({event_type}): {e}")
            yield sse_event('error', {'error': str(e)})
        finally:
            stop_event.set()

    # Wrap subscribe callback so it queues payloads
    def queued_callback(payload):
        if stop_event.is_set():
            return
        q.put(payload)

    # The caller provides subscribe_fn; by default it should enqueue.
    # We ignore provided subscribe_fn and always enqueue to keep behavior consistent.
    # (keeps function signature flexible without breaking.)
    actual_callback = queued_callback

    return generate(), actual_callback


def create_realtime_endpoints(app, cache, db_connection):
    """Create real-time API endpoints for the Flask app."""

    @app.route('/api/realtime/crypto-stream')
    def crypto_stream():
        """SSE stream for crypto updates."""

        def get_initial():
            return cache.get_crypto()

        def to_client(payload):
            # cache.get_crypto() returns list, but subscriber may deliver other shapes.
            if isinstance(payload, dict):
                assets = list(payload.values())
            else:
                assets = payload

            return {
                'assets': assets,
                'count': len(assets) if isinstance(assets, list) else 0,
                'timestamp': datetime.now(timezone.utc).isoformat(),
            }

        stream_gen, queued_callback = _stream_from_cache(
            cache=cache,
            subscribe_key='crypto',
            subscribe_fn=lambda p: None,
            event_type='crypto-update',
            get_initial_payload_fn=get_initial,
            to_client_fn=to_client,
        )

        # Replace placeholder callback by actual queued callback
        def generate():
            # We must recreate with correct callback; easiest: inline logic.
            q: "queue.Queue[Any]" = queue.Queue()
            stop_event = threading.Event()

            def on_update(payload):
                if stop_event.is_set():
                    return
                q.put(payload)

            try:
                initial_payload = get_initial()
                yield sse_event('crypto-update', to_client(initial_payload))
                yield "event: connected\ndata: {\"message\": \"Stream connected\"}\n\n"

                cache.subscribe('crypto', on_update)
                try:
                    while not stop_event.is_set():
                        payload = q.get()
                        yield sse_event('crypto-update', to_client(payload))
                finally:
                    cache.unsubscribe('crypto', on_update)
            except Exception as e:
                logger.error(f"Error in crypto stream: {e}")
                yield sse_event('error', {'error': str(e)})
            finally:
                stop_event.set()

        return app.response_class(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive',
            }
        )

    @app.route('/api/realtime/weather-stream')
    def weather_stream():
        """SSE stream for weather updates."""

        def get_initial():
            return cache.get_weather()

        def to_client(payload):
            # cache.get_weather() returns dict: {location: normalized_entry}
            locations = payload
            count = len(locations) if isinstance(locations, dict) else 0
            return {
                'locations': locations,
                'count': count,
                'timestamp': datetime.now(timezone.utc).isoformat(),
            }

        def generate():
            q: "queue.Queue[Any]" = queue.Queue()
            stop_event = threading.Event()

            def on_update(payload):
                if stop_event.is_set():
                    return
                q.put(payload)

            try:
                initial_payload = get_initial()
                yield sse_event('weather-update', to_client(initial_payload))
                yield "event: connected\ndata: {\"message\": \"Stream connected\"}\n\n"

                cache.subscribe('weather', on_update)
                try:
                    while not stop_event.is_set():
                        payload = q.get()
                        yield sse_event('weather-update', to_client(payload))
                finally:
                    cache.unsubscribe('weather', on_update)
            except Exception as e:
                logger.error(f"Error in weather stream: {e}")
                yield sse_event('error', {'error': str(e)})
            finally:
                stop_event.set()

        return app.response_class(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive',
            }
        )

    @app.route('/api/realtime/social-stream')
    def social_stream():
        """SSE stream for social trends updates."""

        def get_initial():
            return cache.get_social_trends()

        def to_client(payload):
            trends = payload
            return {
                'trends': trends,
                'count': len(trends) if isinstance(trends, list) else 0,
                'timestamp': datetime.now(timezone.utc).isoformat(),
            }

        def generate():
            q: "queue.Queue[Any]" = queue.Queue()
            stop_event = threading.Event()

            def on_update(payload):
                if stop_event.is_set():
                    return
                q.put(payload)

            try:
                initial_payload = get_initial()
                yield sse_event('social-update', to_client(initial_payload))
                yield "event: connected\ndata: {\"message\": \"Stream connected\"}\n\n"

                cache.subscribe('social_trends', on_update)
                try:
                    while not stop_event.is_set():
                        payload = q.get()
                        yield sse_event('social-update', to_client(payload))
                finally:
                    cache.unsubscribe('social_trends', on_update)
            except Exception as e:
                logger.error(f"Error in social stream: {e}")
                yield sse_event('error', {'error': str(e)})
            finally:
                stop_event.set()

        return app.response_class(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive',
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
                'stats': cache.get_all_stats(),
            }
        except Exception as e:
            logger.error(f"Error in get_all_realtime_data: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat(),
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
                'timestamp': datetime.now(timezone.utc).isoformat(),
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
                'timestamp': datetime.now(timezone.utc).isoformat(),
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
                'timestamp': datetime.now(timezone.utc).isoformat(),
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
                'timestamp': datetime.now(timezone.utc).isoformat(),
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
                'timestamp': datetime.now(timezone.utc).isoformat(),
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
                'timestamp': datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.error(f"Error in get_cache_stats: {e}")
            return {'success': False, 'error': str(e)}, 500

    logger.info("Real-time API endpoints registered successfully")

