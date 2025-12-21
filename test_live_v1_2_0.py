#!/usr/bin/env python3
"""
Quick Integration Test for v1.2.0 Features
Tests the live Railway deployment
"""

import requests
import time

def test_live_system():
    """Test the live system is responding"""
    url = "https://exciting-liberation-production.up.railway.app"
    
    print("🚀 Testing Live System v1.2.0")
    print("=" * 50)
    print(f"Target: {url}")
    print()
    
    try:
        # Test web interface is accessible
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print("✅ Web interface accessible")
            
            # Check if it contains expected elements
            content = response.text
            if "Text Space" in content:
                print("✅ Web interface contains expected content")
            else:
                print("❌ Web interface missing expected content")
                
            if "status-bar" in content:
                print("✅ Offline detection UI present")
            else:
                print("❌ Offline detection UI missing")
                
        else:
            print(f"❌ Web interface returned {response.status_code}")
            
    except Exception as e:
        print(f"❌ Web interface test failed: {e}")
    
    print()
    print("📋 Manual Test Checklist for v1.2.0:")
    print("=" * 50)
    print("1. Connect to web interface")
    print("2. Test command: 'version' (should show v1.2.0)")
    print("3. Test aliases: 'l' (look), 'n' (north), 'h' (help)")
    print("4. Test partial matching: 'g green' (go greenhouse)")
    print("5. Test ambiguous matching: 'g ga' (should list options)")
    print("6. Verify room names no longer work as direct commands")
    print()
    print("🔗 Test URL: " + url)

if __name__ == "__main__":
    test_live_system()
