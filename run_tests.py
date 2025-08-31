#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test runner script
"""
import subprocess
import sys
import os

def run_tests():
    """Run all tests"""
    print("Running unit tests...")
    
    # Get the project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Run pytest from the project directory
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests/', 
            '-v', 
            '--tb=short'
        ], cwd=project_dir)
        
        if result.returncode == 0:
            print("\n\u2705 All tests passed!")
        else:
            print("\n\u274c Some tests failed!")
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)