#!/usr/bin/env python3
"""
Simple test script for the LLM endpoint.

This script tests the /api/llm/complete endpoint to ensure it's working correctly.
Run this after starting the Flask application.
"""

import requests
import json
import sys


def test_llm_endpoint():
    """Test the LLM completion endpoint."""
    base_url = "http://localhost:5000"
    
    print("=" * 60)
    print("Testing LLM Completion Endpoint")
    print("=" * 60)
    
    # Test 1: Health check first
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✓ Health check passed")
            print(f"  Response: {response.json()}")
        else:
            print(f"✗ Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Failed to connect to server: {e}")
        print("  Make sure the Flask app is running: python run.py")
        return False
    
    # Test 2: Simple LLM completion
    print("\n2. Testing LLM completion with simple prompt...")
    test_data = {
        "prompt": "What is OpenTelemetry? Answer in one sentence.",
        "max_tokens": 50
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/llm/complete",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"  Status Code: {response.status_code}")
        result = response.json()
        print(f"  Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200:
            print("✓ LLM completion successful")
            if 'completion' in result:
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
            
    except Exception as e:
        print(f"✗ Request failed: {e}")
        return False
    
    # Test 3: Invalid request (missing prompt)
    print("\n3. Testing error handling (missing prompt)...")
    try:
        response = requests.post(
            f"{base_url}/api/llm/complete",
            json={},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 400:
            print("✓ Error handling works correctly")
            print(f"  Response: {response.json()}")
        else:
            print(f"✗ Expected 400, got {response.status_code}")
            
    except Exception as e:
        print(f"✗ Request failed: {e}")
    
    # Test 4: Custom model and temperature
    print("\n4. Testing with custom parameters...")
    test_data = {
        "prompt": "Count from 1 to 5.",
        "temperature": 0.3,
        "max_tokens": 30
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/llm/complete",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Custom parameters work")
            print(f"  Completion: {result.get('completion', 'N/A')[:100]}")
        else:
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.json()}")
            
    except Exception as e:
        print(f"✗ Request failed: {e}")
    
    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Check the OpenLLMetry dashboard for traces")
    print("2. Verify span hierarchy and attributes")
    print("3. Test with different prompts and parameters")
    
    return True


if __name__ == "__main__":
    success = test_llm_endpoint()
    sys.exit(0 if success else 1)

# Made with Bob