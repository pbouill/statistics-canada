# Changelog PAT Setup Guide

This guide explains how to create and configure a Personal Access Token (PAT) for automatic changelog updates that can bypass branch protection rules.

## Step 1: Create Personal Access Token

1. **Go to GitHub Settings**:
   - Navigate to https://github.com/settings/tokens
   - Or: Click your profile → Settings → Developer settings → Personal access tokens → Tokens (classic)

2. **Generate New Token**:
   - Click "Generate new token" → "Generate new token (classic)"
   - **Note**: Use classic tokens, not fine-grained (they have better bypass support)

3. **Configure Token Settings**:
   - **Note**: `changelog-automation-bypass`
   - **Expiration**: Set to "No expiration" (or your preferred duration)
   - **Scopes**: Select the following permissions:
     - ✅ `repo` (Full control of private repositories)
       - This includes: repo:status, repo_deployment, public_repo, repo:invite, security_events
     - ✅ `workflow` (Update GitHub Action workflows)
     - ✅ `write:discussion` (Write team discussions)

4. **Generate and Copy Token**:
   - Click "Generate token"
   - **⚠️ IMPORTANT**: Copy the token immediately - you won't see it again!

## Step 2: Add Token to Repository Secrets

1. **Navigate to Repository Settings**:
   - Go to your repository: https://github.com/pbouill/statistics-canada
   - Click "Settings" tab
   - In left sidebar, click "Secrets and variables" → "Actions"

2. **Create New Repository Secret**:
   - Click "New repository secret"
   - **Name**: `CHANGELOG_PAT`
   - **Secret**: Paste the token you copied in Step 1
   - Click "Add secret"

## Step 3: Configure Branch Protection Bypass

1. **Go to Branch Protection Settings**:
   - Repository Settings → Branches
   - Find your `dev` branch rule, click "Edit"

2. **Add Bypass Permission**:
   - Look for "Restrict pushes that create files"
   - Or find "Allow specified actors to bypass required pull requests"
   - Add your GitHub username to the bypass list
   - ✅ Check "Include administrators" if needed

3. **Alternative Method - Repository Push Rules**:
   - If branch protection is too strict, go to Settings → Rules → Pushes
   - Create or edit push rules to allow PAT-based pushes for changelog files

## Step 4: Test the Setup

1. **Create a Test PR**:
   ```bash
   git checkout dev
   git checkout -b test/changelog-automation
   echo "# Test change" >> README.md
   git add README.md
   git commit -m "test: verify changelog automation"
   git push origin test/changelog-automation
   ```

2. **Create and Merge PR**:
   - Create PR from `test/changelog-automation` to `dev`
   - Merge the PR
   - Watch for the changelog workflow to run

3. **Verify Results**:
   - Check that CHANGELOG.md was updated on dev branch
   - Verify no workflow errors in Actions tab
   - Confirm the commit shows as from "github-actions[bot]"

## Troubleshooting

### Token Permission Issues
- Ensure the PAT has `repo` scope (not just `public_repo`)
- Verify token is not expired
- Check that token belongs to user with admin access to repository

### Branch Protection Still Blocking
- Verify your username is in the bypass list for branch protection
- Consider using "Include administrators" option
- Check if there are organization-level restrictions

### Workflow Still Failing
- Check Actions tab for detailed error messages
- Verify secret name matches exactly: `CHANGELOG_PAT`
- Ensure workflow has proper permissions section

## Security Considerations

1. **Token Scope**: Use minimal necessary scopes
2. **Expiration**: Set reasonable expiration dates
3. **Access**: Only use for automation, not manual operations
4. **Rotation**: Rotate tokens periodically for security

## Alternative Approaches

If PAT approach doesn't work, consider:
1. **GitHub App**: More secure but complex setup
2. **PR-based Changelog**: Create PRs instead of direct pushes
3. **Post-merge Hook**: Update changelog after merge to main

---

**Next Steps**: After completing this setup, your changelog should automatically update when PRs are merged to the `dev` branch, bypassing branch protection rules.
