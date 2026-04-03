#!/usr/bin/env python3
"""
Crypto Data Analysis Script
Command-line tool for analyzing cryptocurrency data
"""

import argparse
import sys
import os
sys.path.append(os.path.dirname(__file__))

from analysis.analyzer import CryptoAnalyzer
from visualization.charts import CryptoVisualizer

def main():
    parser = argparse.ArgumentParser(description='Crypto RPA Data Analysis Tool')
    parser.add_argument('--hours', type=int, default=24,
                       help='Hours of data to analyze (default: 24)')
    parser.add_argument('--symbol', type=str,
                       help='Specific cryptocurrency symbol to analyze')
    parser.add_argument('--action', choices=['summary', 'trends', 'performance', 'volatility', 'alerts', 'report'],
                       default='summary', help='Analysis action to perform')

    args = parser.parse_args()

    analyzer = CryptoAnalyzer()
    visualizer = CryptoVisualizer()

    print(f"🔍 Analyzing cryptocurrency data from the last {args.hours} hours...")
    print("=" * 60)

    if args.action == 'summary':
        summary = analyzer.get_market_summary(args.hours)
        if summary:
            print("📊 MARKET SUMMARY")
            print(f"Total Market Cap:     ${summary['total_market_cap']:,.0f}")
            print(f"Total 24h Volume:     ${summary['total_volume']:,.0f}")
            print(f"Average Price:        ${summary['avg_price']:.2f}")
            print(f"Price Volatility:     ${summary['price_std']:.2f}")
            print(f"Unique Cryptos:       {summary['unique_cryptos']}")
            print(f"Data Points:          {summary['data_points']}")
        else:
            print("❌ No data available")

    elif args.action == 'trends':
        if args.symbol:
            print(f"📈 Price trend for {args.symbol}")
            visualizer.plot_price_trend(args.symbol, args.hours)
        else:
            print("Please specify a symbol with --symbol")

    elif args.action == 'performance':
        print("🏆 TOP PERFORMERS")
        performers = analyzer.get_top_performers(args.hours, 10)
        if performers is not None and not performers.empty:
            for _, row in performers.iterrows():
                change_symbol = "📈" if row['price_change_pct'] >= 0 else "📉"
                print(f"{change_symbol} {row['symbol']}: {row['price_change_pct']:+.2f}% (${row['price_usd_latest']:.2f})")
        else:
            print("❌ No performance data available")

    elif args.action == 'volatility':
        if args.symbol:
            vol = analyzer.calculate_volatility(args.symbol, args.hours)
            if vol is not None:
                print(f"📊 Volatility for {args.symbol}: {vol:.2f}%")
            else:
                print(f"❌ No volatility data for {args.symbol}")
        else:
            print("Please specify a symbol with --symbol")

    elif args.action == 'alerts':
        threshold = 5  # Default 5% threshold
        print(f"⚠️ PRICE ALERTS (>{threshold}% change in last hour)")

        major_cryptos = ['BTC', 'ETH', 'USDT', 'XRP', 'BNB']
        alerts_found = False

        for symbol in major_cryptos:
            alerts = analyzer.detect_price_alerts(symbol, threshold)
            if alerts:
                alerts_found = True
                for alert in alerts[-3:]:  # Show last 3 alerts
                    change_type = "📈 UP" if alert['change_type'] == 'increase' else "📉 DOWN"
                    print(f"{change_type} {symbol}: {alert['change_pct']:+.2f}% (${alert['price']:.2f})")

        if not alerts_found:
            print("✅ No significant alerts detected")

    elif args.action == 'report':
        print("📋 Generating comprehensive report...")
        visualizer.generate_report()
        print("✅ Report generated in 'reports/' directory")

    print("\n" + "=" * 60)
    print("💡 Available actions: summary, trends, performance, volatility, alerts, report")
    print("💡 Use --symbol to focus on specific cryptocurrency")
    print("💡 Use --hours to change time window")

if __name__ == "__main__":
    main()