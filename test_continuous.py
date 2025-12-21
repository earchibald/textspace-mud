#!/usr/bin/env python
"""
Continuous web client testing - runs tests in a loop
"""
import time
import sys
from test_web_client import WebClientTester

def continuous_test(interval=300):  # 5 minutes
    """Run tests continuously"""
    print("🔄 Starting Continuous Web Client Testing")
    print(f"   Interval: {interval} seconds")
    print("   Press Ctrl+C to stop")
    print()
    
    test_count = 0
    pass_count = 0
    
    try:
        while True:
            test_count += 1
            print(f"\n🧪 Test Run #{test_count} - {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 60)
            
            tester = WebClientTester()
            success = tester.run_full_test()
            
            if success:
                pass_count += 1
                print("✅ Test run completed successfully")
            else:
                print("❌ Test run failed")
            
            print(f"\n📈 Stats: {pass_count}/{test_count} passed ({pass_count/test_count*100:.1f}%)")
            
            if test_count < 100:  # Don't run forever
                print(f"⏰ Waiting {interval} seconds until next test...")
                time.sleep(interval)
            else:
                print("🏁 Reached maximum test runs (100)")
                break
                
    except KeyboardInterrupt:
        print(f"\n\n🛑 Testing stopped by user")
        print(f"📊 Final Stats: {pass_count}/{test_count} passed ({pass_count/test_count*100:.1f}%)")

if __name__ == "__main__":
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    continuous_test(interval)
