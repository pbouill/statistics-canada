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

    Args:
        version: Version string for the release (e.g., "1.2.3").

    """
    try:
        with open('CHANGELOG.md') as f:
            content = f.read()

        unreleased_pattern = re.compile(r'## \[UNRELEASED\]', re.IGNORECASE)
        today = datetime.now().isoformat()
        release_header = f'## [{version}] - {today}'

        if not unreleased_pattern.search(content):
            sys.exit(1)

        new_content = unreleased_pattern.sub(release_header, content, count=1)

        with open('CHANGELOG.md', 'w') as f:
            f.write(new_content)


    except FileNotFoundError:
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != _EXPECTED_ARGS:
        sys.exit(1)

    version_arg = sys.argv[1]
    update_changelog(version_arg)
