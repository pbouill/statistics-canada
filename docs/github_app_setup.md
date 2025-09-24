# GitHub App Setup for Changelog Automation

## Overview
This guide sets up a GitHub App specifically for changelog automation that can bypass branch protection rules on the `dev` branch.

## Step 1: Create GitHub App

1. **Navigate to GitHub App Settings**:
   - Go to https://github.com/settings/apps
   - Or: Your profile → Settings → Developer settings → GitHub Apps

2. **Create New GitHub App**:
   - Click "New GitHub App"
   - **GitHub App name**: `changelog-bot-statistics-canada` (must be globally unique)
   - **Description**: `Automated changelog updates for statistics-canada repository`
   - **Homepage URL**: `https://github.com/pbouill/statistics-canada`
   - **Webhook**: Uncheck "Active" (we don't need webhooks)

3. **Configure Permissions**:
   - **Repository permissions**:
     - ✅ **Contents**: `Write` (to modify CHANGELOG.md)
     - ✅ **Pull requests**: `Read` (to read PR information)
     - ✅ **Metadata**: `Read` (required by GitHub)
   - **Organization permissions**: Leave all as "No access"
   - **Account permissions**: Leave all as "No access"

4. **Where can this GitHub App be installed?**:
   - Select "Only on this account"

5. **Create the App**:
   - Click "Create GitHub App"
   - **Save the App ID** - you'll need this for `CHANGELOG_APP_ID`

## Step 2: Generate Private Key

1. **In your new GitHub App page**:
   - Scroll down to "Private keys"
   - Click "Generate a private key"
   - **Download and save the `.pem` file** - you'll need this for `CHANGELOG_APP_PRIVATE_KEY`

## Step 3: Install App on Repository

1. **Install the App**:
   - In your GitHub App page, click "Install App" in the left sidebar
   - Click "Install" next to your account name
   - Select "Only select repositories"
   - Choose **statistics-canada** repository
   - Click "Install"

## Step 4: Add Secrets to Repository

1. **Navigate to Repository Secrets**:
   - Go to https://github.com/pbouill/statistics-canada/settings/secrets/actions
   - Or: Repository → Settings → Secrets and variables → Actions

2. **Add App ID Secret**:
   - Click "New repository secret"
   - **Name**: `CHANGELOG_APP_ID`
   - **Secret**: Paste the App ID from Step 1.5
   - Click "Add secret"

3. **Add Private Key Secret**:
   - Click "New repository secret"
   - **Name**: `CHANGELOG_APP_PRIVATE_KEY`
   - **Secret**: Open the `.pem` file from Step 2.2 and paste the ENTIRE contents (including `-----BEGIN RSA PRIVATE KEY-----` and `-----END RSA PRIVATE KEY-----`)
   - Click "Add secret"

## Step 5: Verification Checklist

Before testing, verify:

- [ ] GitHub App created with name `changelog-bot-statistics-canada`
- [ ] App has **Contents: Write** and **Pull requests: Read** permissions
- [ ] App is installed on `statistics-canada` repository only
- [ ] `CHANGELOG_APP_ID` secret added to repository
- [ ] `CHANGELOG_APP_PRIVATE_KEY` secret added to repository (full `.pem` file contents)
- [ ] Workflow file `dev-changelog.yml` references correct secret names

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
