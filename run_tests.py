#!/usr/bin/env python3
"""Test runner for Stattic with comprehensive reporting."""

import sys
import subprocess
import os
from pathlib import Path

def run_tests():
    """Run all tests with coverage reporting."""
    
    # Change to the stattic directory
    os.chdir(Path(__file__).parent)
    
    print("🧪 Running Stattic Test Suite")
    print("=" * 50)
    
    # Install test requirements
    print("📦 Installing test requirements...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"
        ], check=True, capture_output=True)
        print("✅ Test requirements installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install test requirements: {e}")
        return False
    
    # Run tests with coverage
    print("\n🔍 Running tests with coverage...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/",
            "-v",
            "--cov=stattic",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=80"
        ], check=False)
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
            print("📊 Coverage report generated in htmlcov/")
            return True
        else:
            print(f"\n❌ Tests failed with return code {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def run_security_tests():
    """Run security-specific tests."""
    print("\n🔒 Running security tests...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_security.py",
            "-v"
        ], check=False)
        
        if result.returncode == 0:
            print("✅ Security tests passed!")
            return True
        else:
            print("❌ Security tests failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error running security tests: {e}")
        return False

def run_performance_tests():
    """Run performance-related tests."""
    print("\n⚡ Running performance tests...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_image_processing.py",
            "-v",
            "--durations=10"
        ], check=False)
        
        if result.returncode == 0:
            print("✅ Performance tests passed!")
            return True
        else:
            print("❌ Performance tests failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error running performance tests: {e}")
        return False

def main():
    """Main test runner."""
    success = True
    
    # Run all tests
    if not run_tests():
        success = False
    
    # Run security tests
    if not run_security_tests():
        success = False
    
    # Run performance tests
    if not run_performance_tests():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All test suites completed successfully!")
        print("📈 Check htmlcov/index.html for detailed coverage report")
    else:
        print("💥 Some tests failed. Please review the output above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
