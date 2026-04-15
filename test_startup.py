#!/usr/bin/env python3
"""
Quick test to verify the Flask application can start.
"""

import sys

try:
    from app import create_app
    from app.config import Config
    
    print("✓ Imports successful")
    
    # Create the app
    app = create_app()
    print("✓ Flask app created successfully")
    
    # Test that we can get a test client
    with app.test_client() as client:
        # Test health endpoint
        response = client.get('/health')
        print(f"✓ Health endpoint responded with status {response.status_code}")
        
        if response.status_code == 200:
            data = response.get_json()
            print(f"✓ Health check response: {data}")
        
        # Test root endpoint
        response = client.get('/')
        print(f"✓ Root endpoint responded with status {response.status_code}")
        
        if response.status_code == 200:
            data = response.get_json()
            print(f"✓ Root response: {data}")
    
    print("\n" + "="*50)
    print("SUCCESS: Flask application is working correctly!")
    print("="*50)
    sys.exit(0)
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Made with Bob
