#!/usr/bin/env python3
"""
Organized Test Runner for Statistics Canada Package

This test runner supports the new organized test structure:
- tests/unit/          - Unit tests for core functionality
  - wds/               - WDS API unit tests  
  - sdmx/              - SDMX processing unit tests
- tests/integration/   - Integration tests requiring network/API access
- tests/tools/         - Tests for code generation and utility tools

Usage:
    python tests/run_tests.py              # Run all tests
    python tests/run_tests.py unit         # Run only unit tests
    python tests/run_tests.py wds          # Run only WDS tests
    python tests/run_tests.py integration  # Run only integration tests
    python tests/run_tests.py tools        # Run only tool tests
"""

import sys
import argparse
import subprocess
from pathlib import Path

# Add the project root to the path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_pytest_category(category: str | None = None, verbose: bool = True) -> int:
    """Run tests using pytest for a specific category."""
    tests_dir = Path(__file__).parent
    
    if category == 'unit':
        test_path = tests_dir / 'unit'
    elif category == 'wds':
        test_path = tests_dir / 'unit' / 'wds'
    elif category == 'sdmx':
        test_path = tests_dir / 'unit' / 'sdmx'
    elif category == 'integration':
        test_path = tests_dir / 'integration'
    elif category == 'tools':
        test_path = tests_dir / 'tools'
    else:
        test_path = tests_dir
    
    cmd = [
        sys.executable, "-m", "pytest", 
        str(test_path),
        "-v" if verbose else "-q",
        "--tb=short"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=False)
        return result.returncode
    except FileNotFoundError:
        print("❌ pytest not found. Install with: pip install pytest")
        return 1


def run_unittest_category(category: str | None = None, verbose: bool = True) -> int:
    """Run tests using unittest for a specific category."""
    import unittest
    
    tests_dir = Path(__file__).parent
    loader = unittest.TestLoader()
    
    if category == 'unit':
        suite = loader.discover(str(tests_dir / 'unit'), pattern='test*.py')
    elif category == 'wds':
        suite = loader.discover(str(tests_dir / 'unit' / 'wds'), pattern='test*.py')
    elif category == 'sdmx':
        suite = loader.discover(str(tests_dir / 'unit' / 'sdmx'), pattern='test*.py')
    elif category == 'integration':
        suite = loader.discover(str(tests_dir / 'integration'), pattern='test*.py')
    elif category == 'tools':
        suite = loader.discover(str(tests_dir / 'tools'), pattern='test*.py')
    else:
        # Run all tests
        suite = unittest.TestSuite()
        for subdir in ['unit', 'integration', 'tools']:
            if (tests_dir / subdir).exists():
                sub_suite = loader.discover(str(tests_dir / subdir), pattern='test*.py')
                suite.addTest(sub_suite)
    
    verbosity = 2 if verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


def main():
    parser = argparse.ArgumentParser(description='Run Statistics Canada package tests')
    parser.add_argument(
        'category', 
        nargs='?', 
        choices=['unit', 'wds', 'sdmx', 'integration', 'tools'],
        help='Test category to run (default: all)'
    )
    parser.add_argument(
        '-v', '--verbose', 
        action='store_true',
        default=True,
        help='Verbose output (default: True)'
    )
    parser.add_argument(
        '--unittest',
        action='store_true', 
        help='Force use of unittest instead of pytest'
    )
    
    args = parser.parse_args()
    
    print(f"\n🧪 Running {args.category or 'all'} tests...")
    print("=" * 60)
    
    # Choose test runner
    if args.unittest:
        exit_code = run_unittest_category(args.category, args.verbose)
    else:
        # Try pytest first, fallback to unittest
        try:
            exit_code = run_pytest_category(args.category, args.verbose)
        except:
            print("⚠️  pytest failed, falling back to unittest")
            exit_code = run_unittest_category(args.category, args.verbose)
    
    # Summary
    print("\n" + "=" * 60)
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
        
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
