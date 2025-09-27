
import argparse
import re
import sys

# These patterns are from the original file-patterns.sh script.
PACKAGE_PATTERNS = [
    re.compile(r"^statscan/"),
    re.compile(r"^pyproject\.toml$"),
    re.compile(r"^setup\.py$"),
    re.compile(r"^requirements.*\.txt$"),
    re.compile(r"^README\.md$"),
    re.compile(r"^LICENSE$"),
]

INFRASTRUCTURE_PATTERNS = [
    re.compile(r"^\.github/"),
    re.compile(r"^docs/"),
    re.compile(r"^tools/"),
    re.compile(r"^examples/"),
    re.compile(r"^scratch/"),
    re.compile(r"^tests/.*\.py$"),
]

def should_trigger_package_operations(changed_files):
    """
    Determines if the changed files should trigger package operations.
    """
    for file in changed_files:
        if not file:
            continue

        if any(pattern.match(file) for pattern in PACKAGE_PATTERNS):
            print(f"  ✅ Package-relevant file found: {file}", file=sys.stderr)
            return True

        if any(pattern.match(file) for pattern in INFRASTRUCTURE_PATTERNS):
            print(f"  ⏭️  Infrastructure file: {file}", file=sys.stderr)
            continue

        # Unknown file type - be conservative
        print(f"  ❓ Unknown file type, being conservative: {file}", file=sys.stderr)
        return True

    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check if changed files are package-relevant.")
    parser.add_argument("files", nargs="*", help="List of changed files from stdin.")
    args = parser.parse_args()

    files_to_check = []
    if not sys.stdin.isatty():
        files_to_check.extend(line.strip() for line in sys.stdin)

    if args.files:
        files_to_check.extend(args.files)

    if not files_to_check:
        print("false")
        sys.exit(0)


    if should_trigger_package_operations(files_to_check):
        print("true")
    else:
        print("false")

