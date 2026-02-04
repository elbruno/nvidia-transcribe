#!/usr/bin/env python3
"""
Simple test script to verify the server is working correctly.
"""

import sys
import requests
import time

def test_server(base_url="http://localhost:8000"):
    """Test the server endpoints."""
    
    print(f"Testing server at {base_url}\n")
    
    # Test 1: Root endpoint
    print("1. Testing root endpoint (GET /)...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("   ✓ Root endpoint working")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ✗ Failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    print()
    
    # Test 2: Health check
    print("2. Testing health endpoint (GET /health)...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            health = response.json()
            print(f"   ✓ Health check successful")
            print(f"   Status: {health['status']}")
            print(f"   Model loaded: {health['model_loaded']}")
            print(f"   Model name: {health['model_name']}")
            
            if not health['model_loaded']:
                print("   ⚠ Warning: Model not loaded yet, waiting...")
                time.sleep(5)
                return test_server(base_url)  # Retry
        else:
            print(f"   ✗ Failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    print()
    print("✓ All basic tests passed!")
    print("\nNote: To test transcription, use the console client or web app with an audio file.")
    return True


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    success = test_server(url)
    sys.exit(0 if success else 1)
