import sys
import re
from datetime import datetime

def update_changelog(version):
    """
    Updates the CHANGELOG.md file by replacing the '[UNRELEASED]' section
    with the new version and current date.
    """
    try:
        with open('CHANGELOG.md', 'r') as f:
            content = f.read()

        unreleased_pattern = re.compile(r'## \[UNRELEASED\]', re.IGNORECASE)
        today = datetime.now().isoformat()
        release_header = f'## [{version}] - {today}'

        if not unreleased_pattern.search(content):
            print("Error: '## [UNRELEASED]' section not found in CHANGELOG.md.")
            sys.exit(1)

        new_content = unreleased_pattern.sub(release_header, content, count=1)

        with open('CHANGELOG.md', 'w') as f:
            f.write(new_content)

        print(f"Successfully updated CHANGELOG.md for version {version}.")

    except FileNotFoundError:
        print("Error: CHANGELOG.md not found.")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_release_changelog.py <version>")
        sys.exit(1)
    
    version_arg = sys.argv[1]
    update_changelog(version_arg)