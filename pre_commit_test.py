#!/usr/bin/env python3
"""
Pre-commit test runner
Ensures code quality before deployment
"""

import subprocess
import sys
import time

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"🧪 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def main():
    """Run all pre-commit tests"""
    print("🚀 Pre-commit Test Suite")
    print("=" * 50)
    
    tests = [
        ("python test_v1_2_0.py", "Core functionality tests"),
        ("python -c 'import yaml; yaml.safe_load(open(\"rooms.yaml\"))'", "Validate rooms.yaml"),
        ("python -c 'import yaml; yaml.safe_load(open(\"bots.yaml\"))'", "Validate bots.yaml"),
        ("python -c 'import yaml; yaml.safe_load(open(\"items.yaml\"))'", "Validate items.yaml"),
        ("python -c 'import yaml; yaml.safe_load(open(\"scripts.yaml\"))'", "Validate scripts.yaml"),
        ("python -c 'from server import TextSpaceServer; s = TextSpaceServer()'", "Server initialization"),
        ("python -c 'from server import VERSION; print(f\"Version: {VERSION}\")'", "Version check"),
    ]
    
    passed = 0
    failed = 0
    
    for cmd, desc in tests:
        if run_command(cmd, desc):
            passed += 1
        else:
            failed += 1
    
    print()
    print("📊 Pre-commit Results")
    print("=" * 50)
    print(f"Tests run: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("🎉 All tests passed - ready to commit!")
        return 0
    else:
        print("❌ Some tests failed - fix issues before committing")
        return 1

if __name__ == "__main__":
    sys.exit(main())
