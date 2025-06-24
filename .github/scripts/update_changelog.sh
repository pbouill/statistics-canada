#!/bin/bash
# Update CHANGELOG.md with a new PR entry
# Usage: update_changelog.sh <PR_NUMBER> <PR_TITLE> <PR_USER>

set -e  # Exit on any error

PR_NUMBER="$1"
PR_TITLE="$2"
PR_USER="$3"

# Validate input parameters
if [ -z "$PR_NUMBER" ] || [ -z "$PR_TITLE" ] || [ -z "$PR_USER" ]; then
    echo "Error: Missing required parameters"
    echo "Usage: $0 <PR_NUMBER> <PR_TITLE> <PR_USER>"
    exit 1
fi

# Create changelog entry
CHANGELOG_ENTRY="* $PR_TITLE (#$PR_NUMBER) @$PR_USER"

echo "Adding changelog entry: $CHANGELOG_ENTRY"

# Check if CHANGELOG.md exists
if [ ! -f "CHANGELOG.md" ]; then
    echo "Creating new CHANGELOG.md"
    cat > CHANGELOG.md << 'CHANGELOG_EOF'
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

CHANGELOG_EOF
    echo "$CHANGELOG_ENTRY" >> CHANGELOG.md
    echo "" >> CHANGELOG.md
else
    echo "Updating existing CHANGELOG.md"
    
    # Check if there's an [Unreleased] section
    if grep -q "## \[Unreleased\]" CHANGELOG.md; then
        # Find line number of [Unreleased] section and add entry after it
        LINE_NUM=$(grep -n "## \[Unreleased\]" CHANGELOG.md | head -1 | cut -d: -f1)
        NEXT_LINE=$((LINE_NUM + 1))
        
        # Insert the new entry
        sed -i "${NEXT_LINE}i\\
\\
$CHANGELOG_ENTRY" CHANGELOG.md
    else
        # Add [Unreleased] section after main header
        if grep -q "# Changelog" CHANGELOG.md; then
            LINE_NUM=$(grep -n "# Changelog" CHANGELOG.md | head -1 | cut -d: -f1)
            NEXT_LINE=$((LINE_NUM + 1))
            
            sed -i "${NEXT_LINE}i\\
\\
All notable changes to this project will be documented in this file.\\
\\
## [Unreleased]\\
\\
$CHANGELOG_ENTRY" CHANGELOG.md
        else
            # Prepend everything to existing file
            echo "# Changelog" > CHANGELOG.md.new
            echo "" >> CHANGELOG.md.new
            echo "All notable changes to this project will be documented in this file." >> CHANGELOG.md.new
            echo "" >> CHANGELOG.md.new
            echo "## [Unreleased]" >> CHANGELOG.md.new
            echo "" >> CHANGELOG.md.new
            echo "$CHANGELOG_ENTRY" >> CHANGELOG.md.new
            echo "" >> CHANGELOG.md.new
            cat CHANGELOG.md >> CHANGELOG.md.new
            mv CHANGELOG.md.new CHANGELOG.md
        fi
    fi
fi

echo "CHANGELOG.md updated successfully"
