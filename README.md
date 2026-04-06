# Cloud Bulldozer Skills Marketplace

A centralized marketplace of AI coding skills for the [Cloud Bulldozer](https://github.com/cloud-bulldozer) organization.

Skills are portable markdown instructions that work across Claude Code, Cursor, and any LLM provider (OpenAI, Gemini, Ollama, etc.). Install only what you need.

**Documentation:** [cloud-bulldozer.github.io/org-skills](https://cloud-bulldozer.github.io/org-skills)

## Quick Start

**Claude Code:**
```bash
/plugin marketplace add cloud-bulldozer/org-skills
/plugin install orion@cb-skills
```

**Cursor:**
```bash
curl -fsSL https://raw.githubusercontent.com/cloud-bulldozer/org-skills/main/install-cursor.sh | bash
```

**Any LLM:**
```python
skill = open("orion/skills/orion-regression-analysis/SKILL.md").read()
# Pass as system prompt to any provider
```

## Available Plugins

| Plugin | Skill | Description |
|--------|-------|-------------|
| [orion](orion/) | `orion-regression-analysis` | Performance regression detection for OpenShift CPT — Elasticsearch setup, metric discovery, config generation, and result analysis using [Orion](https://github.com/cloud-bulldozer/orion) |

## Repository Structure

```
org-skills/
├── .claude-plugin/marketplace.json        # Marketplace registry
├── orion/                                 # Orion plugin
│   ├── .claude-plugin/plugin.json         # Plugin metadata
│   └── skills/orion-regression-analysis/  # Skill (from jtaleric/orion-skill)
│       ├── SKILL.md                       # Skill definition
│       ├── docs/                          # Guides, patterns, examples
│       ├── scripts/                       # ES discovery & validation tools
│       └── assets/                        # Config templates
├── skills/                                # Flat directory (Cursor symlinks)
│   └── orion-regression-analysis/ → symlink
├── docs/                                  # Documentation site (GitHub Pages)
└── install-cursor.sh                      # One-command Cursor installer
```

## Contributing

Want to add a skill for your team's workflow? See the guides:

- **[Add a skill](https://cloud-bulldozer.github.io/org-skills/contributing/add-a-skill)** to an existing plugin
- **[Add a plugin](https://cloud-bulldozer.github.io/org-skills/contributing/add-a-plugin)** with new skills

## License

Apache-2.0
