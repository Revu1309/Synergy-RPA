# TODO - Realtime data not showing

## Plan confirmation
- Add real-time UI integration so `dashboard.html` actually loads `static/js/realtime-data-manager.js`.
- Add missing DOM containers used by the JS (`crypto-container`, `weather-container`, `social-container`, `signal-fusion-container`).
- Minimal integration: show the latest received payloads.
- Keep existing `/api/dashboard-data` snapshot/cards.

## Steps
1. Inspect and update `dashboard/templates/dashboard.html`.
2. (If needed) update `static/js/realtime-data-manager.js` so it updates the existing dashboard DOM rather than relying on missing helpers.
3. Run `test_realtime_integration.py` (and/or manual curl/EventSource checks).
4. Verify in browser Network tab: ensure EventSource connections hit `/api/realtime/*`.

