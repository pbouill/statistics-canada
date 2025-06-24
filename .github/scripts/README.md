# GitHub Actions Scripts

This directory contains scripts used by GitHub Actions workflows.

## Scripts

### `update_changelog.sh`

Updates the project's `CHANGELOG.md` file with new PR entries.

**Usage:**
```bash
./update_changelog.sh <PR_NUMBER> <PR_TITLE> <PR_USER>
```

**Parameters:**
- `PR_NUMBER`: The pull request number
- `PR_TITLE`: The title of the pull request
- `PR_USER`: The GitHub username of the PR author

**Behavior:**
- Creates `CHANGELOG.md` if it doesn't exist
- Adds entries under the `[Unreleased]` section
- Creates the `[Unreleased]` section if it doesn't exist
- Maintains proper markdown formatting

**Example:**
```bash
./update_changelog.sh 123 "Add new census data endpoints" "developer"
```

This will add the following entry to `CHANGELOG.md`:
```markdown
* Add new census data endpoints (#123) @developer
```

### `test_changelog.sh`

Test script for `update_changelog.sh` to validate functionality locally.

**Usage:**
```bash
./test_changelog.sh
```

**Features:**
- Creates test scenarios for changelog updates
- Backs up existing `CHANGELOG.md` before testing
- Restores the original file after testing
- Tests various edge cases including special characters

## Development

### Testing Changes

Before modifying `update_changelog.sh`, run the test script to ensure everything works:

```bash
cd /path/to/your/repository
.github/scripts/test_changelog.sh
```

### Syntax Checking

You can use `shellcheck` to validate the shell scripts:

```bash
shellcheck .github/scripts/*.sh
```

### Manual Testing

To manually test the changelog script:

1. Make sure you're in the repository root
2. Run the script with test parameters:
   ```bash
   .github/scripts/update_changelog.sh 999 "Test PR title" "testuser"
   ```
3. Check the `CHANGELOG.md` file to verify the entry was added correctly

## Integration

These scripts are used by the following GitHub Actions workflows:

- `.github/workflows/update-changelog.yml` - Uses `update_changelog.sh` when PRs are merged
- `.github/workflows/publish.yml` - Reads from the changelog for release notes

## File Structure

```
.github/
├── scripts/
│   ├── README.md                 # This file
│   ├── update_changelog.sh       # Main changelog update script
│   └── test_changelog.sh         # Test script for local development
└── workflows/
    ├── update-changelog.yml      # Workflow that uses update_changelog.sh
    └── publish.yml               # Workflow that reads the changelog
```
