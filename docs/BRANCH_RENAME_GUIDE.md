# Branch Rename Guide: master → main

This document outlines the steps required to rename the default branch from `master` to `main` in the nvidia-transcribe repository.

## Why Rename?

Renaming the default branch from `master` to `main`:
- Aligns with modern Git and GitHub conventions (GitHub's default since October 2020)
- Promotes more inclusive terminology in software development
- Matches industry standards adopted by major open-source projects
- Simplifies onboarding for new contributors familiar with `main` convention

## Steps to Rename the Branch

### 1. Rename the Branch on GitHub (Repository Settings)

**This must be done by a repository administrator:**

1. Navigate to the repository on GitHub: https://github.com/elbruno/nvidia-transcribe
2. Click **Settings** (requires admin access)
3. In the left sidebar, click **Branches** under "Code and automation"
4. Under "Default branch", click the pencil icon (✏️) next to the current default branch
5. Select or type `main` as the new default branch name
6. Click **Rename branch**
7. GitHub will automatically:
   - Rename the branch
   - Update branch protection rules
   - Update open pull requests
   - Show instructions for updating local clones

### 2. Update Local Clones

**For all developers with local clones:**

After the branch is renamed on GitHub, update your local repository:

```bash
# Fetch the latest changes from remote
git fetch origin

# Switch to the new main branch
git checkout main

# Update the default branch for your local repository
git branch -u origin/main main

# Optional: Remove old master branch reference
git branch -d master
```

Alternatively, you can use a single command:

```bash
git branch -m master main
git fetch origin
git branch -u origin/main main
git remote set-head origin -a
```

### 3. Update CI/CD Workflows (If Applicable)

If the repository has GitHub Actions workflows or other CI/CD configurations that reference the `master` branch, they will need to be updated.

**Current Status:** As of the date of this document, no workflows were found that reference `master`.

**To verify:**
```bash
grep -r "master" .github/
```

If any workflows are added in the future that reference branch names, ensure they use `main` instead of `master`.

### 4. Update Documentation (If Needed)

**Current Status:** No documentation files currently reference the `master` branch.

If documentation is added in the future that references branch names, ensure it uses `main`.

### 5. Notify Contributors

Once the branch is renamed, notify all contributors:
- Post an issue or discussion explaining the change
- Include the local update commands from Step 2
- Update any contributing guidelines

## Verification

After renaming, verify the change:

1. Check that `main` is now the default branch in GitHub settings
2. Verify that `git clone` retrieves the `main` branch by default
3. Confirm that pull requests target `main` by default
4. Test that CI/CD workflows run correctly

## Rollback (If Needed)

If issues arise, the branch can be renamed back following the same process, substituting `main` with `master`.

## References

- [GitHub: Renaming a branch](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-branches-in-your-repository/renaming-a-branch)
- [GitHub: Inclusive naming](https://github.com/github/renaming)
