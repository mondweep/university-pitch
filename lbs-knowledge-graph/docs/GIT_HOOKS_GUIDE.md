# Git Hooks Guide - LBS Knowledge Graph

This project uses Git hooks to maintain documentation quality and consistency.

## Pre-Commit Hook

### What It Does

The pre-commit hook automatically checks if `README.md` needs updating when you commit changes. It analyzes your staged files and warns you if documentation updates are likely needed.

### Triggers

The hook checks for:

1. **New Documentation Files** (`docs/*.md`, `plans/*.md`)
2. **New Test Scripts** (`scripts/test_*.py`, `tests/*.py`)
3. **New Enrichment Code** (`src/enrichment/*.py`)
4. **Phase Completion Reports** (`PHASE_*_COMPLETE*.md`)
5. **Major Source Changes** (>5 files in core modules)

### How It Works

```
Your commit:
├── docs/NEW_FEATURE.md       ← Detected!
├── scripts/test_feature.py   ← Detected!
└── src/enrichment/feature.py ← Detected!

↓

⚠️  WARNING: README.md may need updating!

Suggestions:
  1. Add link to docs/NEW_FEATURE.md
  2. Update test commands section
  3. Document new enrichment pipeline
```

### Installation

The hook is already installed in `.git/hooks/pre-commit`.

To reinstall or update:

```bash
# Copy hook to .git/hooks/
cp scripts/setup-git-hooks.sh .
chmod +x setup-git-hooks.sh
./setup-git-hooks.sh
```

### Usage Examples

#### Example 1: Adding New Documentation

```bash
# You add a new doc file
git add docs/NEW_API_GUIDE.md
git commit -m "Add new API guide"

# Hook warns you:
# ⚠️  WARNING: README.md may need updating!
# Found new documentation files:
#   - docs/NEW_API_GUIDE.md

# Update README
vim README.md  # Add link to new guide
git add README.md
git commit -m "Add new API guide and update README"
# ✅ Pre-commit checks passed
```

#### Example 2: Completing a Phase

```bash
# You complete Phase 4
git add docs/PHASE_4_COMPLETE_SWARM_REPORT.md
git commit -m "Complete Phase 4"

# Hook warns you:
# ⚠️  WARNING: README.md may need updating!
# Found phase completion reports:
#   - docs/PHASE_4_COMPLETE_SWARM_REPORT.md

# Update README status table
vim README.md  # Update phase status
git add README.md
git commit --amend --no-edit
# ✅ Pre-commit checks passed
```

#### Example 3: Minor Changes (No Warning)

```bash
# Small bug fix
git add src/utils/helpers.py
git commit -m "Fix typo in helper function"
# ✅ Pre-commit checks passed (no README warning)
```

### Bypassing the Hook

If you need to commit without updating README (not recommended):

```bash
git commit --no-verify -m "Emergency fix"
```

**Use sparingly!** The hook is there to maintain documentation quality.

### Validation Checks

When README.md is staged, the hook validates:

1. **Minimum Length**: At least 50 lines (prevents accidental truncation)
2. **Required Sections**: Must have "Overview", "Documentation", "Testing"
3. **Valid Format**: Markdown parsing doesn't fail

### What to Update in README

When the hook triggers, consider updating:

#### For New Documentation:
```markdown
## Documentation

### 📚 Quick Navigation

**New Section:**
- 📄 [Your New Doc](/docs/YOUR_NEW_DOC.md) - Brief description
```

#### For Phase Completion:
```markdown
| Phase | Status | Completion Date | Documentation |
|-------|--------|----------------|---------------|
| **Phase X** | ✅ Complete | Nov X, 2025 | [Phase X Status](/docs/PHASE_X_COMPLETE.md) |
```

#### For New Enrichments:
```markdown
## Enrichment Pipelines

### 3. Your New Enrichment ✅
- **Model**: Your model choice
- **Success Rate**: X%
- **Cost**: $X.XX per item
- **Status**: Production ready
```

#### For New Tests:
```markdown
## Testing

```bash
# Your new test command
python scripts/test_your_feature.py
```
```

### Troubleshooting

#### Hook Not Running

```bash
# Check if hook is executable
ls -l .git/hooks/pre-commit

# Make it executable
chmod +x .git/hooks/pre-commit

# Test manually
.git/hooks/pre-commit
```

#### False Positives

If the hook warns unnecessarily:

```bash
# Option 1: Update README anyway (best practice)
vim README.md
git add README.md

# Option 2: Commit with verification that no update needed
git commit -m "Your message" --no-verify
```

#### Hook Says README Missing Sections

```bash
# View current README structure
grep "^## " README.md

# Add missing sections
vim README.md

# Verify sections exist
grep "^## Overview" README.md
grep "^## Documentation" README.md
grep "^## Testing" README.md
```

### Hook Output Examples

#### Success (README Staged):
```
🔍 Checking if README.md needs updating...
📄 Found new documentation files:
  - docs/NEW_FEATURE.md
✅ README.md updated and staged

📋 Commit Summary:
  Files to commit: 2
  README.md staged: Yes ✅

✅ Pre-commit checks passed
```

#### Warning (README Not Staged):
```
🔍 Checking if README.md needs updating...
📄 Found new documentation files:
  - docs/NEW_FEATURE.md

⚠️  WARNING: README.md may need updating!

Your commit includes changes that typically require README updates:
  - New documentation files
  ...

📝 Please consider updating README.md with:
  1. New documentation links in the 'Quick Navigation' section
  ...

Continue with commit anyway? (y/N):
```

## Best Practices

1. **Always Update README for Documentation Changes**
   - New docs should always be linked from README
   - Keeps navigation up-to-date

2. **Update Phase Status Immediately**
   - When completing a phase, update the status table
   - Link to completion report

3. **Document New Features**
   - Add enrichment pipelines to README
   - Include cost and performance data

4. **Keep Test Commands Current**
   - Update test commands section
   - Show example outputs

5. **Use Descriptive Commit Messages**
   - Good: "Add sentiment analysis pipeline and update README"
   - Bad: "Updates" (doesn't explain what changed)

## Maintenance

### Updating the Hook

```bash
# Edit the hook
vim .git/hooks/pre-commit

# Test changes
git add test_file.py
git commit -m "Test hook" --dry-run

# If issues, restore original
cp scripts/setup-git-hooks.sh .
./setup-git-hooks.sh
```

### Adding New Triggers

To add new patterns that should trigger README updates, edit `.git/hooks/pre-commit`:

```bash
# Add new check (example: API changes)
NEW_API=$(echo "$STAGED_FILES" | grep -E "^src/api/.*\.py$" | wc -l)
if [ "$NEW_API" -gt 0 ]; then
    NEEDS_README_UPDATE=1
    echo -e "${YELLOW}🔌 Found API changes:${NC}"
    echo "$STAGED_FILES" | grep -E "^src/api/.*\.py$" | sed 's/^/  - /'
fi
```

## FAQ

**Q: Can I disable the hook?**
A: Yes, but not recommended. Use `--no-verify` for specific commits.

**Q: Will this work on Windows?**
A: Yes, if you have Git Bash or WSL installed.

**Q: Does this hook modify files?**
A: No, it only checks and warns. You must update README.md manually.

**Q: What if I forget to update README?**
A: The hook will remind you before each commit. You can also update README in a follow-up commit.

**Q: Can I customize the warnings?**
A: Yes, edit `.git/hooks/pre-commit` to adjust triggers and messages.

---

**Tip**: The hook is designed to help, not hinder. If you find it too strict, adjust the thresholds in the script!
