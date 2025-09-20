#!/usr/bin/env python3
"""
Example test demonstrating QA integration for abbreviations validation.
This shows how to use tools/review_abbreviations.py in pytest or CI/CD pipelines.
"""

import subprocess
import sys
from pathlib import Path

def test_abbreviations_validation():
    """Test that abbreviations.py passes all validation checks."""
    
    # Get the project root directory
    project_root = Path(__file__).parent
    script_path = project_root / "tools" / "review_abbreviations.py"
    
    # Run the validation script in QA mode
    result = subprocess.run(
        [sys.executable, str(script_path), "--qa"],
        capture_output=True,
        text=True,
        cwd=project_root
    )
    
    # Check exit codes according to the script's documentation:
    # 0: All checks passed, no issues found
    # 1: Validation errors found (must be fixed) 
    # 2: Consolidation opportunities available (optional optimization)
    # 3: Critical errors (file not found, import failures)
    
    if result.returncode == 0:
        # Perfect - no issues found
        print("✅ Abbreviations validation: All checks passed")
        assert True
    elif result.returncode == 2:
        # Acceptable - consolidation opportunities exist but not errors
        print("⚠️ Abbreviations validation: Consolidation opportunities available")
        print("Consider running tools/resolve_morphological_conflicts.py for optimization")
        assert True  # This is acceptable for tests
    elif result.returncode == 1:
        # Fail - validation errors must be fixed
        print("❌ Abbreviations validation errors found:")
        print(result.stdout)
        assert False, "Abbreviations validation failed - errors must be fixed"
    elif result.returncode == 3:
        # Critical failure
        print("💥 Critical abbreviations validation failure:")
        print(result.stdout)
        print(result.stderr)
        assert False, "Critical abbreviations validation failure"
    else:
        # Unexpected exit code
        assert False, f"Unexpected exit code {result.returncode}"


def test_abbreviations_strict_validation():
    """Test that abbreviations.py has no validation errors (strict mode)."""
    
    project_root = Path(__file__).parent
    script_path = project_root / "tools" / "review_abbreviations.py"
    
    # Run the validation script in check-only mode (no consolidation analysis)
    result = subprocess.run(
        [sys.executable, str(script_path), "--check-only", "--qa"],
        capture_output=True,
        text=True,
        cwd=project_root
    )
    
    # In check-only mode, only 0 (pass) and 1 (errors) are expected
    if result.returncode == 0:
        print("✅ Strict validation: No errors found")
        assert True
    else:
        print("❌ Strict validation failed:")
        print(result.stdout)
        assert False, "Abbreviations has validation errors"


if __name__ == "__main__":
    # Can be run directly for testing
    print("Running abbreviations QA tests...")
    
    try:
        test_abbreviations_validation()
        print("✅ Basic validation test passed")
    except AssertionError as e:
        print(f"❌ Basic validation test failed: {e}")
        sys.exit(1)
    
    try:
        test_abbreviations_strict_validation()
        print("✅ Strict validation test passed")
    except AssertionError as e:
        print(f"❌ Strict validation test failed: {e}")
        sys.exit(1)
    
    print("🎉 All QA tests passed!")
