# Generic GitHub App Setup for Multi-Repository Changelog Automation

## Overview
This guide sets up a GitHub App for changelog automation that can work across multiple repositories and bypass branch protection rules on development branches.

## Step 1: Create GitHub App

1. **Navigate to GitHub App Settings**:
   - Go to https://github.com/settings/apps
   - Or: Your profile → Settings → Developer settings → GitHub Apps

2. **Create New GitHub App**:
   - Click "New GitHub App"
   - **GitHub App name**: `changelog-bot-pbouill` (must be globally unique - use your username)
   - **Description**: `Multi-repository automated changelog updates`
   - **Homepage URL**: `https://github.com/pbouill` (your GitHub profile - simple and professional)
   - **Webhook**: Uncheck "Active" (we don't need webhooks)
   - **Request user authorization (OAuth) during installation**: Leave unchecked
   - **Expire user authorization tokens**: Leave unchecked

3. **Configure Permissions** (Fine-grained Security):
   - **Repository permissions**:
     - ✅ **Contents**: `Write` (to modify changelog files)
       - **File-specific access**: Restrict to `CHANGELOG.md` and `changelog.md` files only
       - This is much more secure than full repository write access
     - ✅ **Pull requests**: `Read` (to read PR information for changelog entries)
     - ✅ **Metadata**: `Read` (required by GitHub for basic repository information)
   - **Organization permissions**: Leave all as "No access"
   - **Account permissions**: Leave all as "No access"
   
   **Security Note**: By restricting Contents access to only changelog files, the app cannot modify any other repository content, making it much safer than broad repository access.

4. **Where can this GitHub App be installed?**:
   - ✅ **Select "Any account"** (Recommended - allows future flexibility)
   - This enables use across different organizations and collaboration scenarios
   - You can always control where it's actually installed through the installation process

5. **Create the App**:
   - Click "Create GitHub App"
   - **Save the App ID** - you'll need this for `CHANGELOG_BOT_APP_ID`

## Step 2: Generate Private Key

1. **In your new GitHub App page**:
   - Scroll down to "Private keys"
   - Click "Generate a private key"
   - **Download and save the `.pem` file** - you'll need this for `CHANGELOG_BOT_PRIVATE_KEY`

## Step 3: Install App on Repositories

1. **Install the App**:
   - In your GitHub App page, click "Install App" in the left sidebar
   - Click "Install" next to your account name
   - Select "All repositories" (recommended for multi-repo use) OR "Only select repositories"
   - If selecting specific repositories, choose the ones where you want changelog automation
   - Click "Install"

2. **For Multiple Repositories**:
   - You can add more repositories later by going to the App's installation page
   - Navigate to Settings → Applications → Installed GitHub Apps → Configure next to your app

## Step 4: Add Secrets to Repository

1. **Navigate to Repository Secrets**:
   - Go to https://github.com/pbouill/statistics-canada/settings/secrets/actions
   - Or: Repository → Settings → Secrets and variables → Actions

2. **Add App ID Secret**:
   - Click "New repository secret"
   - **Name**: `CHANGELOG_BOT_APP_ID`
   - **Secret**: Paste the App ID from Step 1.5
   - Click "Add secret"

3. **Add Private Key Secret**:
   - Click "New repository secret"
   - **Name**: `CHANGELOG_BOT_PRIVATE_KEY`
   - **Secret**: Open the `.pem` file from Step 2.2 and paste the ENTIRE contents (including `-----BEGIN RSA PRIVATE KEY-----` and `-----END RSA PRIVATE KEY-----`)
   - Click "Add secret"

## Step 5: Copy Workflow to Other Repositories

The generic workflow can be copied to any repository with the same two secrets:

1. **Copy the workflow file**: `.github/workflows/dev-changelog.yml` (or rename to `changelog.yml`)
2. **Add the same two secrets** to each repository:
   - `CHANGELOG_BOT_APP_ID`
   - `CHANGELOG_BOT_PRIVATE_KEY`
3. **Optionally customize** the workflow environment variables for each repo:
   - `CHANGELOG_FILE`: Default is `CHANGELOG.md`
   - `CHANGELOG_SCRIPT`: Custom script path if you have one
   - Target branches: Add/remove branches in the `on.pull_request.branches` list

## Step 6: Verification Checklist

Before testing, verify:

- [ ] GitHub App created with name `changelog-bot-pbouill` (or similar)
- [ ] App has **Contents: Write** permission (restricted to changelog files only)
- [ ] App has **Pull requests: Read** permission  
- [ ] App has **Metadata: Read** permission (required by GitHub)
- [ ] App is installed on target repositories
- [ ] `CHANGELOG_BOT_APP_ID` secret added to each repository
- [ ] `CHANGELOG_BOT_PRIVATE_KEY` secret added to each repository (full `.pem` file contents)
- [ ] Workflow file references correct secret names

## Security Validation

With file-specific permissions, verify:
- [ ] App can only access `CHANGELOG.md` and `changelog.md` files
- [ ] App cannot access other repository files (source code, configs, etc.)
- [ ] App has minimal necessary permissions for changelog automation
- [ ] Branch protection bypass works only for changelog file changes

## Step 6: Test Setup

Run the end-to-end test:
```bash
# Create test branch and PR
git checkout dev
git pull origin dev
git checkout -b test/github-app-changelog
echo "# Test GitHub App Integration" >> README.md
git add README.md
git commit -m "test: verify GitHub App changelog automation"
git push origin test/github-app-changelog

# Create PR via GitHub CLI
gh pr create --title "Test: GitHub App Changelog Integration" --body "Testing the GitHub App-based changelog automation system." --base dev --head test/github-app-changelog
```

## Expected Results

After merging the test PR:
1. Workflow should run without authentication errors
2. CHANGELOG.md should be updated on dev branch
3. Commit should show as from "changelog-bot[bot]"
4. No branch protection violations should occur
5. PR should receive comment confirming changelog update

## Troubleshooting

### "Bad credentials" Error
- Verify `CHANGELOG_APP_PRIVATE_KEY` contains the complete `.pem` file
- Ensure no extra spaces or line breaks in the secret

### "App not installed" Error
- Verify app is installed on the `statistics-canada` repository
- Check app has correct permissions (Contents: Write, Pull requests: Read)

### "Repository rule violations" Error
- This should NOT happen with GitHub App - if it does, verify:
  - App is properly installed with bypass capabilities
  - Secrets are correctly configured
  - App has Contents: Write permission

### Workflow doesn't trigger
- Verify PR is merged to `dev` branch (not main)
- Check workflow file is on the target branch (`dev`)

---

**Ready to proceed with setup?** Follow steps 1-4, then we'll run the test in Step 6.
