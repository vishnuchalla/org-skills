---
layout: default
title: Cloud Bulldozer Skills Marketplace
---

<div class="hero">
  <h1>Cloud Bulldozer <span class="highlight">Skills</span></h1>
  <p>AI coding skills that work across Claude Code, Cursor, and any LLM. Shared by the org, installed in seconds.</p>
  <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap">
    <a href="{{ '/setup/claude-code' | relative_url }}" class="btn btn-primary">Get Started</a>
    <a href="{{ '/skills/orion' | relative_url }}" class="btn btn-secondary">Browse Skills</a>
  </div>
</div>

## What Are Skills?

Skills are markdown files (`SKILL.md`) that give an AI assistant expert-level instructions for a specific task. They're portable — the same skill works whether you're using Claude Code, Cursor, the Claude API, or any other LLM.

This marketplace is a shared, version-controlled collection of skills maintained by the Cloud Bulldozer organization.

## Available Plugins

<div class="cards">
  <div class="card">
    <h3>Orion</h3>
    <p>Performance regression detection for OpenShift CPT benchmarks. Guides you through Elasticsearch setup, metric discovery, Orion YAML config generation, and result analysis.</p>
    <code>/orion-regression-analysis</code>
  </div>
</div>

> Want to add a skill? See [Contributing]({{ '/contributing/add-a-skill' | relative_url }}).

<div class="quick-install">

## Quick Install

### Claude Code

```bash
# Register the marketplace (one-time)
/plugin marketplace add cloud-bulldozer/org-skills

# Install the Orion plugin
/plugin install orion@cb-skills
```

### Cursor

```bash
curl -fsSL https://raw.githubusercontent.com/cloud-bulldozer/org-skills/main/install-cursor.sh | bash
```

### Any LLM (OpenAI, Gemini, Ollama, etc.)

Skills are just markdown — read the file and pass it as a system prompt:

```python
skill = open("orion/skills/orion-regression-analysis/SKILL.md").read()
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": skill},
        {"role": "user", "content": "Help me build an Orion config for cluster-density-v2 on AWS"}
    ]
)
```

</div>

## How It Works

Skills are loaded differently depending on the tool:

| Tool | How Skills Are Loaded | Install |
|------|----------------------|---------|
| **Claude Code** | Native plugin system — auto-triggers on context | `/plugin install orion@cb-skills` |
| **Cursor** | Flat `skills/` directory | `install-cursor.sh` or `npx skills add` |
| **OpenAI / Gemini / Ollama** | Pass `SKILL.md` content as system prompt | Read the file |
| **Claude Agent SDK** | Load via `settingSources: ["project"]` | Clone repo into project |
| **CI/CD (GitHub Actions)** | `anthropics/claude-code@v1` action | See [setup guide]({{ '/setup/claude-code' | relative_url }}) |

## Repository Layout

```
org-skills/
├── .claude-plugin/marketplace.json        # Marketplace registry
├── <plugin-name>/                         # One directory per plugin
│   ├── .claude-plugin/plugin.json         # Plugin metadata (name, version)
│   └── skills/<skill-name>/              # One directory per skill
│       ├── SKILL.md                       # Skill definition (required)
│       ├── docs/                          # Reference guides (optional)
│       ├── scripts/                       # Utility scripts (optional)
│       └── assets/                        # Templates, configs (optional)
├── skills/                                # Flat symlinks for Cursor
├── docs/                                  # This documentation site
└── install-cursor.sh                      # Cursor installer
```
