#!/bin/bash
# Test script for update_changelog.sh
# This helps validate the changelog update functionality locally

set -e

SCRIPT_DIR="$(dirname "$0")"
CHANGELOG_SCRIPT="$SCRIPT_DIR/update_changelog.sh"

# Cleanup function
cleanup() {
    if [ -f "CHANGELOG.md.backup" ]; then
        echo "Restoring original CHANGELOG.md..."
        mv CHANGELOG.md.backup CHANGELOG.md
    fi
    if [ -f "test_CHANGELOG.md" ]; then
        rm test_CHANGELOG.md
    fi
}

# Set up cleanup on exit
trap cleanup EXIT

echo "🧪 Testing changelog update script..."
echo

# Backup existing CHANGELOG.md if it exists
if [ -f "CHANGELOG.md" ]; then
    cp CHANGELOG.md CHANGELOG.md.backup
    echo "📋 Backed up existing CHANGELOG.md"
fi

# Test 1: Create new changelog
echo "Test 1: Creating new changelog..."
rm -f CHANGELOG.md
$CHANGELOG_SCRIPT 123 "Add new feature for data processing" "testuser"

if [ -f "CHANGELOG.md" ]; then
    echo "✅ CHANGELOG.md created successfully"
    echo "📄 Content:"
    cat CHANGELOG.md
    echo
else
    echo "❌ Failed to create CHANGELOG.md"
    exit 1
fi

# Test 2: Add to existing changelog with [Unreleased] section
echo "Test 2: Adding to existing changelog..."
$CHANGELOG_SCRIPT 124 "Fix bug in DGUID parsing" "contributor"

echo "✅ Entry added to existing changelog"
echo "📄 Updated content:"
cat CHANGELOG.md
echo

# Test 3: Add another entry
echo "Test 3: Adding another entry..."
$CHANGELOG_SCRIPT 125 "Update documentation with examples" "docwriter"

echo "✅ Second entry added"
echo "📄 Final content:"
cat CHANGELOG.md
echo

# Test 4: Test with special characters
echo "Test 4: Testing with special characters..."
$CHANGELOG_SCRIPT 126 "Fix issue with [brackets] and \$pecial chars" "specialuser"

echo "✅ Special characters handled"
echo "📄 Content with special chars:"
tail -5 CHANGELOG.md
echo

echo "🎉 All tests passed!"
echo
echo "💡 To run this test script:"
echo "   cd /path/to/your/repo"
echo "   .github/scripts/test_changelog.sh"
