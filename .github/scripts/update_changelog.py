
import argparse
import os
import re

CHANGELOG_PATH = "CHANGELOG.md"
UNRELEASED_HEADER = "## [Unreleased]"
CHANGELOG_TEMPLATE = f"# Changelog\n\nAll notable changes to this project will be documented in this file.\n\nThe format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),\nand this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n\n{UNRELEASED_HEADER}\n"

def update_changelog(pr_number, pr_title, pr_author, pr_url):
    """
    Updates the CHANGELOG.md file with a new entry.
    """
    entry = f"- {pr_title} ([#{pr_number}]({pr_url})) by @{pr_author}"

    if not os.path.exists(CHANGELOG_PATH):
        print(f"Creating new {CHANGELOG_PATH}")
        with open(CHANGELOG_PATH, "w") as f:
            f.write(CHANGELOG_TEMPLATE)
            f.write(f"\n{entry}\n")
        return

    with open(CHANGELOG_PATH, "r+") as f:
        content = f.read()

        if f"([#{pr_number}]" in content:
            print(f"Entry for PR #{pr_number} already exists in changelog.")
            return

        unreleased_match = re.search(r"^## [Unreleased]", content, re.MULTILINE)

        if unreleased_match:
            insert_pos = unreleased_match.end()
            new_content = content[:insert_pos] + f"\n\n{entry}" + content[insert_pos:]
            f.seek(0)
            f.write(new_content)
            print("Added entry to changelog.")
        else:
            # This case should be rare if the file is created from the template
            print("Could not find [Unreleased] section in changelog. Adding it.")
            # Just prepend the entry at the top for now.
            # A more robust solution could be to find the first `##` and insert before it.
            new_content = CHANGELOG_TEMPLATE + f"\n{entry}\n\n" + content
            f.seek(0)
            f.write(new_content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update CHANGELOG.md with a new PR entry.")
    parser.add_argument("pr_number", help="The PR number.")
    parser.add_argument("pr_title", help="The PR title.")
    parser.add_argument("pr_author", help="The PR author's username.")
    parser.add_argument("pr_url", help="The URL of the PR.")
    args = parser.parse_args()

    update_changelog(args.pr_number, args.pr_title, args.pr_author, args.pr_url)
