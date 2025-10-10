"""Update CHANGELOG.md for releases.

This script replaces the [UNRELEASED] section with a versioned release
header during the release process. Used in CI/CD release workflows.
"""

import re
import sys
from datetime import datetime

_EXPECTED_ARGS = 2  # script name + version


def update_changelog(version):
    """Update the CHANGELOG.md file for a new release.

    Replaces the '[UNRELEASED]' section with the new version and current date.
    Prevents duplicate version headers by checking if the version already exists.

    Args:
        version: Version string for the release (e.g., "1.2.3").

    """
    try:
        with open('CHANGELOG.md') as f:
            content = f.read()

        # Check if this version already has a header
        version_exists_pattern = re.compile(
            rf'## \[{re.escape(version)}\]', re.IGNORECASE
        )
        if version_exists_pattern.search(content):
            print(f"Version {version} already exists in CHANGELOG.md. Skipping update.")
            return

        unreleased_pattern = re.compile(r'## \[UNRELEASED\]', re.IGNORECASE)
        today = datetime.now().strftime('%Y-%m-%d')
        release_header = f'## [{version}] - {today}'

        if not unreleased_pattern.search(content):
            print("ERROR: No [UNRELEASED] section found in CHANGELOG.md")
            sys.exit(1)

        # Replace [UNRELEASED] with version header (only first occurrence)
        new_content = unreleased_pattern.sub(release_header, content, count=1)

        with open('CHANGELOG.md', 'w') as f:
            f.write(new_content)

        print(f"Successfully updated CHANGELOG.md with version {version}")

    except FileNotFoundError:
        print("ERROR: CHANGELOG.md not found")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != _EXPECTED_ARGS:
        sys.exit(1)

    version_arg = sys.argv[1]
    update_changelog(version_arg)
