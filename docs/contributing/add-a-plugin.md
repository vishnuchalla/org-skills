---
layout: default
title: Contributing — Add a Plugin
---

# Add a New Plugin

A plugin groups related skills under one installable unit. Create a new plugin when your skills cover a distinct domain that doesn't fit an existing plugin.

## Plugin Structure

```
<plugin-name>/
├── .claude-plugin/
│   └── plugin.json        # Required — plugin metadata
└── skills/
    └── <skill-name>/
        └── SKILL.md        # At least one skill required
```

## Step by Step

### 1. Create the directory

```bash
mkdir -p <plugin-name>/.claude-plugin
mkdir -p <plugin-name>/skills/<skill-name>
```

### 2. Write `plugin.json`

```json
{
  "name": "<plugin-name>",
  "version": "1.0.0",
  "description": "What this plugin provides",
  "author": {
    "name": "Cloud Bulldozer Team"
  }
}
```

- `name` must match the directory name (kebab-case)
- `version` follows [semver](https://semver.org)

### 3. Write your skill(s)

See [Add a Skill]({{ '/contributing/add-a-skill' | relative_url }}) for the `SKILL.md` format.

### 4. Register in `marketplace.json`

Add an entry to `.claude-plugin/marketplace.json` in the repo root:

```json
{
  "name": "<plugin-name>",
  "version": "1.0.0",
  "source": "./<plugin-name>",
  "description": "What this plugin provides",
  "license": "Apache-2.0"
}
```

### 5. Add Cursor symlinks

For each skill:

```bash
mkdir -p skills/<plugin>-<skill>
ln -s ../../<plugin>/skills/<skill>/SKILL.md skills/<plugin>-<skill>/SKILL.md
```

### 6. Add a doc page

Create `docs/skills/<plugin>.md` and add it to the sidebar in `docs/_layouts/default.html`.

### 7. Submit

```bash
git checkout -b add-plugin/<name>
git add <name>/ skills/<name>-* .claude-plugin/marketplace.json docs/skills/<name>.md
git commit -m "Add <name> plugin"
gh pr create --title "Add <name> plugin"
```

## After Merging

Users install with:

```bash
/plugin install <plugin-name>@cb-skills
```

## Naming Guidelines

- **Kebab-case**: `kube-burner`, `incident-response`
- **Name by domain**, not team: `benchmarking` not `perf-team-tools`
- **Keep it short**: 1-2 words

## Full Example

After adding a `benchmarking` plugin, the repo looks like:

```
org-skills/
├── .claude-plugin/
│   └── marketplace.json              # Updated with new entry
├── orion/                            # Existing
│   ├── .claude-plugin/plugin.json
│   └── skills/orion-regression-analysis/
├── benchmarking/                     # New plugin
│   ├── .claude-plugin/plugin.json
│   └── skills/run-benchmark/SKILL.md
├── skills/
│   ├── orion-regression-analysis/    # Existing symlink
│   └── benchmarking-run-benchmark/   # New symlink
└── docs/
    └── skills/
        ├── orion.md                  # Existing
        └── benchmarking.md           # New doc page
```
