#!/bin/bash
# Setup Git Hooks for LBS Knowledge Graph
# This script installs pre-commit hooks to maintain documentation quality

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🔧 Setting up Git hooks for LBS Knowledge Graph${NC}"
echo ""

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}⚠️  Not in a Git repository. Run this from the project root.${NC}"
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Install pre-commit hook
echo -e "${BLUE}📝 Installing pre-commit hook...${NC}"

cat > .git/hooks/pre-commit << 'HOOK_CONTENT'
#!/bin/bash
# Pre-commit hook to remind updating README.md
# This ensures documentation stays current with code changes

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Checking if README.md needs updating...${NC}"

# Get list of staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)

# Check if README.md is already staged
README_STAGED=$(echo "$STAGED_FILES" | grep -c "^README.md$")

# Categories of changes that should trigger README update
NEEDS_README_UPDATE=0

# Check for new documentation files
NEW_DOCS=$(echo "$STAGED_FILES" | grep -E "^docs/.*\.md$|^plans/.*\.md$" | wc -l)
if [ "$NEW_DOCS" -gt 0 ]; then
    NEEDS_README_UPDATE=1
    echo -e "${YELLOW}📄 Found new documentation files:${NC}"
    echo "$STAGED_FILES" | grep -E "^docs/.*\.md$|^plans/.*\.md$" | sed 's/^/  - /'
fi

# Check for new test scripts
NEW_TESTS=$(echo "$STAGED_FILES" | grep -E "^scripts/test_.*\.py$|^tests/.*\.py$" | wc -l)
if [ "$NEW_TESTS" -gt 0 ]; then
    NEEDS_README_UPDATE=1
    echo -e "${YELLOW}🧪 Found new test files:${NC}"
    echo "$STAGED_FILES" | grep -E "^scripts/test_.*\.py$|^tests/.*\.py$" | sed 's/^/  - /'
fi

# Check for new enrichment scripts
NEW_ENRICHMENTS=$(echo "$STAGED_FILES" | grep -E "^src/enrichment/.*\.py$|^scripts/enrichment_.*\.py$" | wc -l)
if [ "$NEW_ENRICHMENTS" -gt 0 ]; then
    NEEDS_README_UPDATE=1
    echo -e "${YELLOW}🤖 Found new enrichment files:${NC}"
    echo "$STAGED_FILES" | grep -E "^src/enrichment/.*\.py$|^scripts/enrichment_.*\.py$" | sed 's/^/  - /'
fi

# Check for phase completion reports
PHASE_REPORTS=$(echo "$STAGED_FILES" | grep -E "PHASE_[0-9]+.*COMPLETE.*\.md$" | wc -l)
if [ "$PHASE_REPORTS" -gt 0 ]; then
    NEEDS_README_UPDATE=1
    echo -e "${YELLOW}📊 Found phase completion reports:${NC}"
    echo "$STAGED_FILES" | grep -E "PHASE_[0-9]+.*COMPLETE.*\.md$" | sed 's/^/  - /'
fi

# Check for major source code changes
MAJOR_SRC_CHANGES=$(echo "$STAGED_FILES" | grep -E "^src/(crawler|parser|graph|enrichment)/.*\.py$" | wc -l)
if [ "$MAJOR_SRC_CHANGES" -gt 5 ]; then
    NEEDS_README_UPDATE=1
    echo -e "${YELLOW}⚙️  Found significant source code changes ($MAJOR_SRC_CHANGES files)${NC}"
fi

# If changes need README update but it's not staged
if [ "$NEEDS_README_UPDATE" -eq 1 ] && [ "$README_STAGED" -eq 0 ]; then
    echo ""
    echo -e "${RED}⚠️  WARNING: README.md may need updating!${NC}"
    echo ""
    echo -e "${YELLOW}Your commit includes changes that typically require README updates:${NC}"
    echo "  - New documentation files"
    echo "  - New test scripts or enrichments"
    echo "  - Phase completion reports"
    echo "  - Major source code changes"
    echo ""
    echo -e "${BLUE}📝 Please consider updating README.md with:${NC}"
    echo "  1. New documentation links in the 'Quick Navigation' section"
    echo "  2. Updated phase status if completing a phase"
    echo "  3. New enrichment pipeline information"
    echo "  4. Updated test commands"
    echo ""
    echo -e "${YELLOW}To update README.md:${NC}"
    echo "  1. Edit README.md with relevant changes"
    echo "  2. git add README.md"
    echo "  3. git commit --amend --no-edit (or make new commit)"
    echo ""
    echo -e "${BLUE}To skip this check and commit anyway:${NC}"
    echo "  git commit --no-verify"
    echo ""

    # Ask if they want to continue
    read -p "$(echo -e ${YELLOW}'Continue with commit anyway? (y/N): '${NC})" -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Commit cancelled. Please update README.md and try again.${NC}"
        exit 1
    fi
fi

# If README is staged, validate it's not empty
if [ "$README_STAGED" -eq 1 ]; then
    README_SIZE=$(git show :README.md | wc -l)
    if [ "$README_SIZE" -lt 50 ]; then
        echo -e "${RED}❌ ERROR: README.md appears too short ($README_SIZE lines)${NC}"
        echo "This might indicate an accidental truncation."
        exit 1
    fi

    # Check for basic required sections
    REQUIRED_SECTIONS=("Overview" "Documentation" "Testing")
    MISSING_SECTIONS=""

    for section in "${REQUIRED_SECTIONS[@]}"; do
        if ! git show :README.md | grep -q "## $section"; then
            MISSING_SECTIONS="$MISSING_SECTIONS\n  - $section"
        fi
    done

    if [ ! -z "$MISSING_SECTIONS" ]; then
        echo -e "${YELLOW}⚠️  WARNING: README.md is missing required sections:${NC}"
        echo -e "$MISSING_SECTIONS"
        echo ""
        read -p "$(echo -e ${YELLOW}'Continue anyway? (y/N): '${NC})" -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}Commit cancelled. Please add missing sections.${NC}"
            exit 1
        fi
    fi

    echo -e "${GREEN}✅ README.md updated and staged${NC}"
fi

# Final check: Show summary
echo ""
echo -e "${GREEN}📋 Commit Summary:${NC}"
echo "  Files to commit: $(echo "$STAGED_FILES" | wc -l)"
echo "  README.md staged: $([ "$README_STAGED" -eq 1 ] && echo 'Yes ✅' || echo 'No')"
echo ""

# Success
echo -e "${GREEN}✅ Pre-commit checks passed${NC}"
exit 0
HOOK_CONTENT

# Make hook executable
chmod +x .git/hooks/pre-commit

echo -e "${GREEN}✅ Pre-commit hook installed${NC}"
echo ""

# Test the hook
echo -e "${BLUE}🧪 Testing the hook...${NC}"
if [ -x .git/hooks/pre-commit ]; then
    echo -e "${GREEN}✅ Hook is executable${NC}"
else
    echo -e "${YELLOW}⚠️  Hook is not executable (this shouldn't happen)${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Git hooks setup complete!${NC}"
echo ""
echo -e "${BLUE}The pre-commit hook will now:${NC}"
echo "  1. Check for new documentation files"
echo "  2. Remind you to update README.md when needed"
echo "  3. Validate README.md structure"
echo "  4. Help maintain documentation quality"
echo ""
echo -e "${YELLOW}📚 Learn more:${NC} docs/GIT_HOOKS_GUIDE.md"
echo ""
