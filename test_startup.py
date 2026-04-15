#!/usr/bin/env python3
"""
Quick test to verify the Flask application can start.
"""

import sys
import traceback


def main():
    """Run a manual startup verification without side effects on import."""
    try:
        from app import create_app

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

        print(f"\n{'=' * 50}")
        print("SUCCESS: Flask application is working correctly!")
        print("=" * 50)
        return 0

    except Exception as exc:  # pylint: disable=broad-exception-caught
        print(f"\n✗ ERROR: {exc}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
