# This file is deprecated - please use app_new.py instead
# This file is kept for backward compatibility

import sys
import os

# Import from the new app file
if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from dashboard.app_new import app
    app.run(debug=False, use_reloader=False, host='0.0.0.0', port=5000)

# Old code below for reference
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import re
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Lazy initialization of components
analyzer = None
visualizer = None

def get_analyzer():
    global analyzer
    if analyzer is None:
        print("Initializing CryptoAnalyzer...")
        from analysis.analyzer import CryptoAnalyzer
        analyzer = CryptoAnalyzer()
        print("CryptoAnalyzer initialized")
    return analyzer

def get_visualizer():
    global visualizer
    if visualizer is None:
        print("Initializing CryptoVisualizer...")
        from visualization.charts import CryptoVisualizer
        visualizer = CryptoVisualizer()
        print("CryptoVisualizer initialized")
    return visualizer

app = Flask(__name__)
CORS(app)
print("Flask app created")


def _extract_legacy_parts(rendered_html):
    head_match = re.search(r"<head[^>]*>(.*?)</head>", rendered_html, flags=re.IGNORECASE | re.DOTALL)
    body_match = re.search(r"<body[^>]*>(.*?)</body>", rendered_html, flags=re.IGNORECASE | re.DOTALL)
    title_match = re.search(r"<title[^>]*>(.*?)</title>", rendered_html, flags=re.IGNORECASE | re.DOTALL)
    head = head_match.group(1) if head_match else ""
    body = body_match.group(1) if body_match else rendered_html
    title = title_match.group(1).strip() if title_match else None
    head = re.sub(r"<title[^>]*>.*?</title>", "", head, flags=re.IGNORECASE | re.DOTALL)
    body = _strip_legacy_navigation(body)
    return title, head, body


def _strip_legacy_navigation(body_html):
    cleaned = body_html or ""
    patterns = [
        r"<nav\b[^>]*>.*?</nav>",
        r"<aside\b[^>]*>.*?</aside>",
        r"<(div|header)[^>]*class=[\"'][^\"']*(?:topbar|top|navbar|header)[^\"']*[\"'][^>]*>.*?(?:/menu|/menu-v2|logout\(\)|window\.location\.href='/menu').*?</\1>",
    ]
    for pattern in patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(
        r"<a\b[^>]*href=[\"']/menu(?:-v2)?[\"'][^>]*>.*?</a>",
        "",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )
    cleaned = re.sub(
        r"<button\b[^>]*(?:onclick=[\"'][^\"']*?/menu[^\"']*[\"'])[^>]*>.*?</button>",
        "",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return cleaned


def render_legacy_template(template_source, **context):
    rendered = app.jinja_env.from_string(template_source).render(**context, request=request)
    page_title, legacy_head, page_content = _extract_legacy_parts(rendered)
    return render_template(
        "legacy_page.html",
        page_title=page_title,
        legacy_head=legacy_head,
        page_content=page_content,
    )

# HTML template

# Advanced Dashboard Template

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template("legacy_crypto_dashboard.html")

@app.route('/api/dashboard-data')
def get_dashboard_data():
    """API endpoint for dashboard data"""
    try:
        analyzer = get_analyzer()
        visualizer = get_visualizer()

        # Get latest data
        df = analyzer.get_recent_data(hours=24)

        if df.empty:
            return jsonify({
                'error': 'No data available',
                'metrics': {},
                'charts': {},
                'alerts': []
            })

        # Calculate metrics
        metrics = analyzer.calculate_metrics(df)

        # Generate charts
        charts = {}
        try:
            price_chart = visualizer.create_price_chart(df)
            if price_chart:
                charts['price_chart'] = price_chart.to_json()

            volume_chart = visualizer.create_volume_chart(df)
            if volume_chart:
                charts['volume_chart'] = volume_chart.to_json()

            market_cap_chart = visualizer.create_market_cap_chart(df)
            if market_cap_chart:
                charts['market_cap_chart'] = market_cap_chart.to_json()

            # New advanced charts
            candlestick_chart = visualizer.create_candlestick_chart('BTC', hours_back=24)
            if candlestick_chart:
                charts['candlestick_chart'] = candlestick_chart.to_json()

            correlation_chart = visualizer.create_correlation_heatmap()
            if correlation_chart:
                charts['correlation_chart'] = correlation_chart.to_json()

            performance_chart = visualizer.create_performance_comparison_chart()
            if performance_chart:
                charts['performance_chart'] = performance_chart.to_json()

            risk_chart = visualizer.create_risk_metrics_chart()
            if risk_chart:
                charts['risk_chart'] = risk_chart.to_json()

            ma_chart = visualizer.create_moving_averages_chart('BTC', hours_back=168)
            if ma_chart:
                charts['ma_chart'] = ma_chart.to_json()

            volume_ratio_chart = visualizer.create_volume_price_ratio_chart()
            if volume_ratio_chart:
                charts['volume_ratio_chart'] = volume_ratio_chart.to_json()

            price_dist_chart = visualizer.create_price_distribution_chart()
            if price_dist_chart:
                charts['price_dist_chart'] = price_dist_chart.to_json()

        except Exception as e:
            print(f"Chart generation error: {e}")

        # Get alerts
        alerts = analyzer.get_price_alerts(df)

        return jsonify({
            'metrics': metrics,
            'charts': charts,
            'alerts': alerts
        })

    except Exception as e:
        print(f"Dashboard data error: {e}")
        return jsonify({
            'error': str(e),
            'metrics': {},
            'charts': {},
            'alerts': []
        })

@app.route('/api/crypto-data')
def get_crypto_data():
    """API endpoint for raw crypto data"""
    try:
        analyzer = get_analyzer()
        hours = int(request.args.get('hours', 24))
        df = analyzer.get_recent_data(hours=hours)
        return jsonify(df.to_dict('records'))
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/analysis/<symbol>')
def get_symbol_analysis(symbol):
    """API endpoint for symbol-specific analysis"""
    try:
        analyzer = get_analyzer()
        hours = int(request.args.get('hours', 24))
        analysis = analyzer.analyze_symbol(symbol.upper(), hours=hours)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/advanced-dashboard')
def get_advanced_dashboard():
    """API endpoint for advanced dashboard with all chart types"""
    try:
        visualizer = get_visualizer()

        # Generate comprehensive dashboard
        dashboard_chart = visualizer.create_advanced_dashboard()
        if dashboard_chart:
            return jsonify({'dashboard': dashboard_chart.to_json()})
        else:
            return jsonify({'error': 'Unable to generate advanced dashboard'})

    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/advanced')
def advanced_dashboard():
    """Advanced dashboard page with comprehensive analytics"""
    return render_template("legacy_advanced_crypto_dashboard.html")

if __name__ == '__main__':
    print("Starting Flask dashboard...")
    # Run in production mode when called from main.py
    import sys
    debug_mode = '--debug' in sys.argv or len(sys.argv) == 1  # Enable debug only when explicitly requested
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
