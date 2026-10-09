#!/usr/bin/env python3
"""
Quick test script untuk verifikasi production setup
"""
import sys
sys.path.insert(0, '.')

from core import FreeReelsClient

def test_client():
    print("="*70)
    print("Testing FreeReels Client...")
    print("="*70)
    
    # Initialize
    client = FreeReelsClient()
    print("[OK] Client initialized")
    
    # Anonymous login
    success = client.login_anonymous()
    if success:
        print("[OK] Anonymous login successful")
        print(f"     User: {client.user_id}")
    else:
        print("[FAIL] Login failed")
        return False
    
    # Test endpoint
    resp = client._request("GET", "/frv2-api/homepage/v2/tab/list")
    if resp and "list" in resp:
        print(f"[OK] API request working ({len(resp['list'])} tabs)")
    else:
        print("[FAIL] API request failed")
        return False
    
    print("\n" + "="*70)
    print("All tests passed! Production setup is ready.")
    print("="*70)
    return True

if __name__ == "__main__":
    test_client()
