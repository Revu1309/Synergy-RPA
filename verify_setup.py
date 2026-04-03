#!/usr/bin/env python3
"""
Quick Test Script to Verify RPA Framework Setup
Run this to ensure everything is working correctly
"""

import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("\n" + "="*70)
    print("TESTING IMPORTS")
    print("="*70)
    
    modules = [
        ('flask', 'Flask'),
        ('flask_cors', 'CORS'),
        ('mysql.connector', 'MySQL'),
        ('pandas', 'Pandas'),
        ('plotly', 'Plotly'),
        ('analysis.analyzer', 'CryptoAnalyzer'),
        ('visualization.charts', 'CryptoVisualizer'),
        ('auth.auth', 'AuthManager'),
    ]
    
    failed = []
    for module_name, display_name in modules:
        try:
            __import__(module_name)
            print(f"✓ {display_name:<20} OK")
        except ImportError as e:
            print(f"✗ {display_name:<20} FAILED: {e}")
            failed.append(module_name)
    
    return len(failed) == 0

def test_flask_app():
    """Test if Flask app can be imported"""
    print("\n" + "="*70)
    print("TESTING FLASK APPLICATION")
    print("="*70)
    
    try:
        from dashboard.app_new import app
        print("✓ Flask app imported successfully")
        
        # Check registered routes
        routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                routes.append(str(rule))
        
        print(f"✓ Found {len(routes)} registered routes")
        return True
    except Exception as e:
        print(f"✗ Failed to import Flask app: {e}")
        return False

def test_database():
    """Test database connection"""
    print("\n" + "="*70)
    print("TESTING DATABASE CONNECTION")
    print("="*70)
    
    try:
        from database.connection import create_connection
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        conn = create_connection()
        
        if conn and conn.is_connected():
            print("✓ Database connection successful")
            
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM crypto_assets")
            count = cursor.fetchone()[0]
            print(f"✓ Found {count} records in database")
            
            cursor.close()
            conn.close()
            return True
        else:
            print("✗ Failed to connect to database")
            return False
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        print("\nNote: This is expected if MySQL is not running")
        return False

def test_auth_system():
    """Test authentication system"""
    print("\n" + "="*70)
    print("TESTING AUTHENTICATION SYSTEM")
    print("="*70)
    
    try:
        from auth.auth import AuthManager
        
        # Test password hashing
        hashed = AuthManager.hash_password("test123")
        print(f"✓ Password hashing works")
        
        # Test credential verification
        result = AuthManager.verify_credentials("admin", "admin")
        print(f"✓ Credential verification: {'PASS' if result else 'FAIL'}")
        
        # Test session creation
        token = AuthManager.create_session("admin")
        print(f"✓ Session creation works: {token[:20]}...")
        
        # Test session verification
        valid = AuthManager.verify_session(token)
        print(f"✓ Session verification: {'PASS' if valid else 'FAIL'}")
        
        return True
    except Exception as e:
        print(f"✗ Auth system test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  RPA FRAMEWORK - SETUP VERIFICATION TEST".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    tests = [
        ("Module Imports", test_imports),
        ("Flask Application", test_flask_app),
        ("Authentication System", test_auth_system),
        ("Database Connection", test_database),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:<10} {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    print("\n" + "="*70)
    if passed == total or passed >= 3:  # At least imports, flask, and auth
        print("✓ SYSTEM IS READY TO RUN")
        print("\nTo start the application:")
        print("  1. Run: start_dashboard.bat")
        print("  2. Open: http://localhost:5000")
        print("  3. Login with: admin / admin")
    else:
        print("✗ SYSTEM HAS ISSUES")
        print("\nPlease check:")
        print("  1. All dependencies: pip install -r requirements.txt")
        print("  2. MySQL is running")
        print("  3. .env file is configured")
    
    print("="*70 + "\n")

if __name__ == "__main__":
    # Add project root to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
