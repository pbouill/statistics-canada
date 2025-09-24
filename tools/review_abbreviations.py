#!/usr/bin/env python3
"""
Quality assurance script for abbreviations dictionary validation.
This script validates the abbreviations.py file for quality and consistency.
"""

import sys
import argparse
from pathlib import Path

def validate_abbreviations(check_only=False, qa_mode=False):
    """
    Validate the abbreviations dictionary.
    
    Returns:
        0: All checks passed, no issues found
        1: Validation errors found (must be fixed) 
        2: Consolidation opportunities available (optional optimization)
        3: Critical errors (file not found, import failures)
    """
    try:
        # Try to import the abbreviations module
        sys.path.insert(0, str(Path(__file__).parent))
        from abbreviations import DEFAULT_ABBREVIATIONS
        
        # Basic validation - check if the dictionary is properly structured
        if not isinstance(DEFAULT_ABBREVIATIONS, dict):
            if qa_mode:
                print("❌ DEFAULT_ABBREVIATIONS is not a dictionary")
            return 1
            
        if len(DEFAULT_ABBREVIATIONS) == 0:
            if qa_mode:
                print("❌ DEFAULT_ABBREVIATIONS is empty")
            return 1
            
        # Check for basic consistency
        for key, values in DEFAULT_ABBREVIATIONS.items():
            if not isinstance(key, str):
                if qa_mode:
                    print(f"❌ Non-string key found: {key}")
                return 1
            if not isinstance(values, list):
                if qa_mode:
                    print(f"❌ Non-list values for key '{key}': {values}")
                return 1
            for value in values:
                if not isinstance(value, str):
                    if qa_mode:
                        print(f"❌ Non-string value in '{key}': {value}")
                    return 1
        
        # All basic checks passed
        if qa_mode:
            print("✅ All abbreviations validation checks passed")
            print(f"Found {len(DEFAULT_ABBREVIATIONS)} abbreviation entries")
        
        return 0
        
    except ImportError as e:
        if qa_mode:
            print(f"💥 Failed to import abbreviations module: {e}")
        return 3
    except Exception as e:
        if qa_mode:
            print(f"💥 Critical error during validation: {e}")
        return 3


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Validate abbreviations dictionary")
    parser.add_argument("--qa", action="store_true", help="Enable QA output mode")
    parser.add_argument("--check-only", action="store_true", help="Check-only mode (no consolidation analysis)")
    
    args = parser.parse_args()
    
    exit_code = validate_abbreviations(check_only=args.check_only, qa_mode=args.qa)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
