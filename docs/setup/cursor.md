---
layout: default
title: Setup — Cursor
---

# Cursor

## Installation

### Option 1: Install Script (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/cloud-bulldozer/org-skills/main/install-cursor.sh | bash
```

Copies all skills to `~/.cursor/skills/`. Restart Cursor to pick them up.

### Option 2: npx

```bash
npx skills add cloud-bulldozer/org-skills
```

### Option 3: Manual

```bash
git clone --depth 1 https://github.com/cloud-bulldozer/org-skills.git /tmp/org-skills
mkdir -p ~/.cursor/skills
cp -r /tmp/org-skills/skills/*/ ~/.cursor/skills/
rm -rf /tmp/org-skills
```

## Using Skills in Cursor

**Reference as context** in chat:

```
@file:~/.cursor/skills/orion-regression-analysis/SKILL.md
Help me build an Orion config for cluster-density-v2 on AWS
```

**Add to project rules** (`.cursorrules` or Cursor Settings > Rules for AI):

```
When asked about Orion configs, performance regressions, or OpenShift
benchmarks, follow the instructions in:
~/.cursor/skills/orion-regression-analysis/SKILL.md
```

## Updating

Re-run the install script — it overwrites with the latest version:

```bash
curl -fsSL https://raw.githubusercontent.com/cloud-bulldozer/org-skills/main/install-cursor.sh | bash
```
