"""
Test runner for the statistics-canada package.
Run with pytest: python -m pytest unittests/ -v
Run with unittest: python -m unittest discover -s unittests -v
"""
import sys
import subprocess
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_with_pytest():
    """Run all tests with pytest."""
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(Path(__file__).parent),
            "-v", "--tb=short"
        ], capture_output=False)
        return result.returncode
    except FileNotFoundError:
        print("pytest not found. Install with: pip install pytest")
        return 1


def run_with_unittest():
    """Run all tests with unittest (fallback)."""
    import unittest
    
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1


def run_specific_test_module(module_name, use_pytest=True):
    """Run tests from a specific module."""
    if use_pytest:
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                str(Path(__file__).parent / f"{module_name}.py"),
                "-v", "--tb=short"
            ], capture_output=False)
            return result.returncode
        except FileNotFoundError:
            print("pytest not found, falling back to unittest")
            use_pytest = False
    
    if not use_pytest:
        import unittest
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
        # Try pytest first, fallback to unittest
        try:
            exit_code = run_with_pytest()
        except:
            print("Failed to run with pytest, using unittest")
            exit_code = run_with_unittest()
    
    sys.exit(exit_code)
