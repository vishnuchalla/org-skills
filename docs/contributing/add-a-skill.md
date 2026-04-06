---
layout: default
title: Contributing — Add a Skill
---

# Add a New Skill

A skill is a `SKILL.md` file that lives inside a plugin. If your skill belongs with an existing plugin, add it there. Otherwise, [create a new plugin]({{ '/contributing/add-a-plugin' | relative_url }}) first.

## What Goes in a Skill

At minimum, a skill is a single `SKILL.md` file. Larger skills can include supporting docs, scripts, and assets:

```
<plugin>/skills/<skill-name>/
├── SKILL.md             # Required — skill definition
├── docs/                # Optional — reference guides, patterns
├── scripts/             # Optional — utility scripts
├── assets/              # Optional — templates, config files
└── docs/examples/       # Optional — sample configs/outputs
```

## Writing SKILL.md

Every `SKILL.md` has YAML frontmatter followed by markdown instructions.

### Frontmatter

```yaml
---
name: my-skill-name
description: >-
  One-paragraph description of what this skill does and when to use it.
  This text drives auto-triggering — include keywords users would say.
user-invocable: true
disable-model-invocation: false
allowed-tools: Read Grep Glob Bash Write
argument-hint: "[file-or-directory]"
---
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Slash command name. Kebab-case, max 64 chars. |
| `description` | Yes | When to use this skill. 150-250 chars recommended. Keywords here drive auto-triggering, so be specific. |
| `user-invocable` | No | Show in the `/` menu. Default: `true`. |
| `disable-model-invocation` | No | Prevent auto-triggering. Set `true` for skills with side effects (deploys, destructive ops). Default: `false`. |
| `allowed-tools` | No | Space-separated tool list: `Read Grep Glob Bash Edit Write`. Restricts what the skill can do. |
| `argument-hint` | No | Autocomplete hint: `"[file]"`, `"<env> [--flag]"`. |

### Markdown Body

Write clear instructions the AI follows when the skill activates. Tips:

- **Be specific.** Vague instructions produce vague results. Include exact steps, field names, and output formats.
- **Use `$ARGUMENTS`** for the full user input after the slash command. Use `$1`, `$2` for positional args.
- **Define a process.** Numbered steps work better than unstructured prose.
- **Show the output format.** If you want structured output (YAML, tables, reports), include an example.
- **Add reference docs** in a `docs/` subdirectory for complex domains. The skill can reference them with relative paths.

### Example

Here's a minimal skill that validates Kubernetes manifests:

```markdown
---
name: validate-manifests
description: >-
  Validate Kubernetes YAML manifests for common issues — missing labels,
  resource limits, security context, and deprecated API versions.
  Use when reviewing k8s configs before applying.
allowed-tools: Read Grep Glob
argument-hint: "[file-or-directory]"
---

You are a Kubernetes configuration expert.

## Process

1. If `$ARGUMENTS` is provided, read those files. Otherwise, find all
   `*.yaml` and `*.yml` files in the current directory.
2. For each manifest, check:
   - Required labels exist (app, version, team)
   - Resource requests and limits are set
   - Security context is not running as root
   - API version is not deprecated
3. Output a findings table sorted by severity.
```

## Adding the Cursor Symlink

Create a flat entry in `skills/` so Cursor can discover it:

```bash
mkdir -p skills/<plugin>-<skill>
ln -s ../../<plugin>/skills/<skill>/SKILL.md skills/<plugin>-<skill>/SKILL.md
```

## Adding Documentation

Update (or create) the plugin's doc page at `docs/skills/<plugin>.md`. Add a section for your new skill with:

- What it does
- Example prompts
- Links to supporting docs if any

If it's a new plugin, add it to the sidebar in `docs/_layouts/default.html`.

## Submitting

```bash
git checkout -b add-skill/<name>
git add <plugin>/skills/<name>/ skills/<plugin>-<name>/ docs/skills/
git commit -m "Add <name> skill to <plugin> plugin"
gh pr create --title "Add <name> skill to <plugin>"
```

### Checklist

- [ ] `SKILL.md` has `name` and `description` in frontmatter
- [ ] Symlink created in `skills/` for Cursor
- [ ] Doc page updated in `docs/skills/`
- [ ] Tested locally with `/plugin install` and skill invocation
