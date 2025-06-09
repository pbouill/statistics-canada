"""
Test runner for the statistics-canada package.
Run all tests with: python -m unittest discover -s unittests -v
"""
import unittest
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_all_tests():
    """Run all unit tests."""
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1


def run_specific_test_module(module_name):
    """Run tests from a specific module."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(f'unittests.{module_name}')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Run specific test module
        module = sys.argv[1]
        exit_code = run_specific_test_module(module)
    else:
        # Run all tests
        exit_code = run_all_tests()
    
    sys.exit(exit_code)
