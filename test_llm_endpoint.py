#!/usr/bin/env python3
"""
Simple manual test script for the LLM endpoint.

This script tests the /api/llm/complete endpoint to ensure it's working correctly.
Run this after starting the Flask application.
"""

import json
import sys

import requests


def run_llm_endpoint_check():
    """Run a manual check of the LLM completion endpoint."""
    base_url = "http://localhost:5000"

    print("=" * 60)
    print("Testing LLM Completion Endpoint")
    print("=" * 60)

    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✓ Health check passed")
            print(f"  Response: {response.json()}")
        else:
            print(f"✗ Health check failed with status {response.status_code}")
            return False
    except requests.RequestException as exc:
        print(f"✗ Failed to connect to server: {exc}")
        print("  Make sure the Flask app is running: uv run python run.py")
        return False

    print("\n2. Testing LLM completion with simple prompt...")
    test_data = {
        "prompt": "What is OpenTelemetry? Answer in one sentence.",
        "max_tokens": 50,
    }

    try:
        response = requests.post(
            f"{base_url}/api/llm/complete",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        print(f"  Status Code: {response.status_code}")
        result = response.json()
        print(f"  Response: {json.dumps(result, indent=2)}")

        if response.status_code == 200:
            print("✓ LLM completion successful")
            if "completion" in result:
                print(f"  Completion: {result['completion'][:100]}...")
                print(f"  Tokens: {result.get('tokens', 'N/A')}")
                print(f"  Latency: {result.get('latency_ms', 'N/A')}ms")
        elif response.status_code == 503:
            print("✗ Ollama is not available")
            print("  Make sure Ollama is running: ollama serve")
            print("  And the model is pulled: ollama pull llama2")
            return False
        else:
            print(f"✗ Request failed with status {response.status_code}")
            return False

    except requests.RequestException as exc:
        print(f"✗ Request failed: {exc}")
        return False

    print("\n3. Testing error handling (missing prompt)...")
    try:
        response = requests.post(
            f"{base_url}/api/llm/complete",
            json={},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        if response.status_code == 400:
            print("✓ Error handling works correctly")
            print(f"  Response: {response.json()}")
        else:
            print(f"✗ Expected 400, got {response.status_code}")

    except requests.RequestException as exc:
        print(f"✗ Request failed: {exc}")

    print("\n4. Testing with custom parameters...")
    test_data = {
        "prompt": "Count from 1 to 5.",
        "temperature": 0.3,
        "max_tokens": 30,
    }

    try:
        response = requests.post(
            f"{base_url}/api/llm/complete",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        if response.status_code == 200:
            result = response.json()
            print("✓ Custom parameters work")
            print(f"  Completion: {result.get('completion', 'N/A')[:100]}")
        else:
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.json()}")

    except requests.RequestException as exc:
        print(f"✗ Request failed: {exc}")

    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Check the OpenLLMetry dashboard for traces")
    print("2. Verify span hierarchy and attributes")
    print("3. Test with different prompts and parameters")

    return True


if __name__ == "__main__":
    sys.exit(run_llm_endpoint_check())

# Made with Bob
