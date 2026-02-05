# Branch Rename Checklist: master → main

This checklist guides repository administrators through renaming the default branch from `master` to `main`.

## Pre-Rename Checklist

- [ ] Verify all CI/CD workflows are working correctly on current branch
- [ ] Check for any hardcoded references to `master` in:
  - [ ] GitHub Actions workflows (`.github/workflows/`)
  - [ ] Documentation files (`*.md`)
  - [ ] Configuration files
  - [ ] Scripts
- [ ] Notify all active contributors about the upcoming change
- [ ] Document the date/time of the planned rename

## Rename Process

### Step 1: Rename Branch on GitHub

1. [ ] Navigate to repository Settings
2. [ ] Go to Branches → Default branch
3. [ ] Click the pencil icon next to current default
4. [ ] Type `main` as new branch name
5. [ ] Click "Rename branch"
6. [ ] Confirm the rename action

**Expected Result:** GitHub automatically updates:
- Branch protection rules
- Open pull requests
- Default branch for new clones

### Step 2: Update Local Development

1. [ ] Post update instructions to all contributors:

```bash
# Update your local repository
git fetch origin
git checkout main
git branch -u origin/main main

# Remove old master branch (optional)
git branch -d master

# Set remote HEAD
git remote set-head origin -a
```

### Step 3: Verify the Rename

- [ ] Clone repository fresh and verify `main` is checked out
- [ ] Create a test pull request and verify it targets `main`
- [ ] Check that branch protection rules are active on `main`
- [ ] Verify CI/CD workflows trigger correctly on `main`

## Post-Rename Tasks

- [ ] Update any external services that reference the branch:
  - [ ] CI/CD systems (if external to GitHub Actions)
  - [ ] Deployment pipelines
  - [ ] Documentation sites
  - [ ] Badge URLs in README (if they reference branch)
- [ ] Close this issue once all steps are complete

## Rollback Plan

If critical issues arise:

1. [ ] Contact all contributors to pause work
2. [ ] Use GitHub Settings to rename `main` back to `master`
3. [ ] Investigate and fix the root cause
4. [ ] Plan a new rename attempt

## Additional Resources

- See `/docs/BRANCH_RENAME_GUIDE.md` for detailed instructions
- [GitHub Official Guide](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-branches-in-your-repository/renaming-a-branch)

---

**Date Completed:** _________________
**Completed By:** _________________
