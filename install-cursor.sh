#!/usr/bin/env bash
#
# Install org-skills into Cursor's skills directory.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/vishnuchalla/org-skills/main/install-cursor.sh | bash
#

set -euo pipefail

REPO="vishnuchalla/org-skills"
BRANCH="main"
SKILLS_DIR="$HOME/.cursor/skills"
TEMP_DIR=$(mktemp -d)

cleanup() { rm -rf "$TEMP_DIR"; }
trap cleanup EXIT

echo "Installing org-skills into Cursor..."

echo "  Cloning $REPO..."
git clone --depth 1 --branch "$BRANCH" "https://github.com/$REPO.git" "$TEMP_DIR" 2>/dev/null

mkdir -p "$SKILLS_DIR"

for skill_dir in "$TEMP_DIR"/skills/*/; do
  [ -d "$skill_dir" ] || continue
  skill_name=$(basename "$skill_dir")

  # Resolve symlink to get the actual SKILL.md content
  if [ -L "$skill_dir/SKILL.md" ]; then
    src=$(cd "$TEMP_DIR" && realpath "$skill_dir/SKILL.md" 2>/dev/null || readlink -f "$skill_dir/SKILL.md")
  else
    src="$skill_dir/SKILL.md"
  fi

  if [ -f "$src" ]; then
    mkdir -p "$SKILLS_DIR/$skill_name"
    cp "$src" "$SKILLS_DIR/$skill_name/SKILL.md"
    echo "  Installed: $skill_name"
  fi
done

echo ""
echo "Done! Skills installed to $SKILLS_DIR"
echo "Restart Cursor to pick up the new skills."
