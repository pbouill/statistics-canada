"""Update CHANGELOG.md with new pull request entries.

This script automatically adds PR entries to the Unreleased section
of CHANGELOG.md. Used in CI/CD workflows after PR merges.
"""

import argparse
import os
import re

CHANGELOG_PATH = "CHANGELOG.md"
UNRELEASED_HEADER = "## [Unreleased]"
CHANGELOG_TEMPLATE = (
    "# Changelog\n\n"
    "All notable changes to this project will be documented in this file.\n\n"
    "The format is based on [Keep a Changelog]"
    "(https://keepachangelog.com/en/1.0.0/),\n"
    "and this project adheres to [Semantic Versioning]"
    "(https://semver.org/spec/v2.0.0.html).\n\n"
    f"{UNRELEASED_HEADER}\n"
)

def update_changelog(pr_number, pr_title, pr_author, pr_url):
    """Update the CHANGELOG.md file with a new entry.

    Args:
        pr_number: Pull request number.
        pr_title: Title of the pull request.
        pr_author: GitHub username of PR author.
        pr_url: URL to the pull request.

    """
    entry = f"- {pr_title} ([#{pr_number}]({pr_url})) by @{pr_author}"

    if not os.path.exists(CHANGELOG_PATH):
        with open(CHANGELOG_PATH, "w") as f:
            f.write(CHANGELOG_TEMPLATE)
            f.write(f"\n{entry}\n")
        return

    with open(CHANGELOG_PATH) as f:
        content = f.read()

    # Check if an entry for this PR already exists and update it
    pr_pattern = rf"^- .+ \(\[#{pr_number}\]\(.+?\)\) by @.+$"
    existing_match = re.search(pr_pattern, content, re.MULTILINE)

    if existing_match:
        # Replace the existing entry with the new one
        new_content = (
            content[:existing_match.start()]
            + entry
            + content[existing_match.end():]
        )
    else:
        # Add new entry after the Unreleased header
        unreleased_match = re.search(r"^## \[Unreleased\]", content, re.MULTILINE)

        if unreleased_match:
            # Find the position right after the header line
            insert_pos = unreleased_match.end()
            # Add entry after header with proper spacing
            new_content = content[:insert_pos] + f"\n\n{entry}" + content[insert_pos:]
        else:
            # No Unreleased section exists - add one at the top
            # Find the first occurrence of "# Changelog" to insert after it
            changelog_header = re.search(r"^# Changelog", content, re.MULTILINE)
            if changelog_header:
                # Insert after the header and any following blank lines/description
                insert_pos = changelog_header.end()
                # Skip to after the description lines if they exist
                remaining_content = content[insert_pos:]
                description_end = re.search(r"\n\n", remaining_content)
                if description_end:
                    insert_pos += description_end.end()

                new_content = (
                    content[:insert_pos]
                    + f"\n{UNRELEASED_HEADER}\n\n{entry}\n"
                    + content[insert_pos:]
                )
            else:
                # No changelog header at all - prepend everything
                new_content = CHANGELOG_TEMPLATE + f"\n{entry}\n\n" + content

    # Write the updated content, truncating the file first
    with open(CHANGELOG_PATH, "w") as f:
        f.write(new_content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Update CHANGELOG.md with a new PR entry."
    )
    parser.add_argument("pr_number", help="The PR number.")
    parser.add_argument("pr_title", help="The PR title.")
    parser.add_argument("pr_author", help="The PR author's username.")
    parser.add_argument("pr_url", help="The URL of the PR.")
    args = parser.parse_args()

    update_changelog(args.pr_number, args.pr_title, args.pr_author, args.pr_url)
