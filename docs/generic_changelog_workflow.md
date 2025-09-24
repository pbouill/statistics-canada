# Generic Changelog Workflow Template

Copy this workflow to any repository where you want automatic changelog updates.

## Quick Setup

1. **Copy workflow file** to `.github/workflows/changelog.yml` (or any name you prefer)
2. **Add repository secrets**:
   - `CHANGELOG_BOT_APP_ID`: Your GitHub App ID
   - `CHANGELOG_BOT_PRIVATE_KEY`: Your GitHub App private key (.pem file contents)
3. **Customize** the configuration variables if needed

## Configuration Options

The workflow supports these environment variables for customization:

```yaml
env:
  # Changelog file name (default: CHANGELOG.md)
  CHANGELOG_FILE: 'CHANGELOG.md'
  
  # Custom changelog script path (optional)
  # If this file exists, it will be used instead of built-in logic
  CHANGELOG_SCRIPT: '.github/scripts/update_changelog.sh'
  
  # Bot identity for commits
  BOT_NAME: 'changelog-bot[bot]'
  BOT_EMAIL: 'changelog-bot[bot]@users.noreply.github.com'
```

## Supported Branch Patterns

The workflow triggers on PRs merged to these branches:
- `dev`, `develop`, `development` (common development branches)
- `main` (if you want changelog updates on main branch too)

You can customize the branch list in the workflow:

```yaml
on:
  pull_request:
    types: [closed]
    branches: 
      - dev
      - develop  
      - main
      # Add your custom branches here
```

## Custom Changelog Script

If you have a custom changelog script, place it at the path specified in `CHANGELOG_SCRIPT`. The script will receive these arguments:

```bash
your_script.sh <PR_NUMBER> <PR_TITLE> <PR_AUTHOR>
```

Example script interface:
```bash
#!/bin/bash
PR_NUMBER="$1"
PR_TITLE="$2"
PR_AUTHOR="$3"

# Your custom changelog logic here
echo "Adding PR #$PR_NUMBER: $PR_TITLE by @$PR_AUTHOR to changelog"
```

## Built-in Changelog Logic

If no custom script is found, the workflow uses built-in logic that:

1. **Creates changelog** if it doesn't exist with standard header
2. **Adds [Unreleased] section** if missing
3. **Inserts new entries** under the [Unreleased] section
4. **Formats entries** as: `- PR_TITLE (#PR_NUMBER) by @PR_AUTHOR`

## Multiple Repository Usage

The same GitHub App can be used across multiple repositories:

1. **Install the GitHub App** on all target repositories
2. **Copy the workflow file** to each repository
3. **Add the same two secrets** to each repository
4. **Customize configuration** per repository if needed

## Repository-Specific Customization Examples

### Python Project
```yaml
env:
  CHANGELOG_FILE: 'HISTORY.md'
  BOT_NAME: 'python-changelog-bot[bot]'
```

### JavaScript Project  
```yaml
env:
  CHANGELOG_FILE: 'CHANGELOG.md'
  CHANGELOG_SCRIPT: '.github/scripts/js_changelog.sh'
```

### Documentation Project
```yaml
on:
  pull_request:
    types: [closed]
    branches: [main, docs]  # Only main and docs branches
```

## Troubleshooting

### Common Issues

1. **Workflow doesn't trigger**:
   - Verify PR is merged to a configured branch
   - Check that workflow file exists on the target branch

2. **"Bad credentials" error**:
   - Verify `CHANGELOG_BOT_PRIVATE_KEY` contains complete .pem file
   - Ensure no extra spaces or characters in the secret

3. **"App not installed" error**:
   - Verify GitHub App is installed on the repository
   - Check App has Contents: Write permission

4. **Branch protection violations**:
   - This shouldn't happen with GitHub Apps (they have inherent bypass)
   - If it occurs, verify App installation and permissions

### Debugging

Enable workflow debugging by setting repository variables:
- `ACTIONS_STEP_DEBUG`: `true`
- `ACTIONS_RUNNER_DEBUG`: `true`

---

**Ready to use!** This workflow provides a clean, reusable solution for automatic changelog management across multiple repositories.
