---
layout: default
title: Setup — Claude Code
---

# Claude Code

## Installation

```bash
# Step 1: Register the Cloud Bulldozer marketplace (one-time)
/plugin marketplace add cloud-bulldozer/org-skills

# Step 2: Install the plugin you need
/plugin install orion@cb-skills
```

That's it. The skill is now available in your session.

## Using Skills

**Slash command** — invoke directly:

```
/orion-regression-analysis
```

**Natural language** — skills auto-trigger when your request matches their description:

```
> Help me build an Orion config for cluster-density-v2 on AWS
> I need to detect regressions in etcd performance across OCP 4.17 runs
> What benchmarks are available in my Elasticsearch data?
```

**Reload after updates:**

```
/reload-plugins
```

## CI/CD and Headless Mode

Run skills non-interactively with `claude -p`:

```bash
# Generate a config
claude -p "Create an Orion config for node-density on AWS with 24 workers" \
  --allowedTools "Skill,Read,Write,Bash" \
  --output-format json

# Bare mode (faster, skips local config discovery)
claude --bare -p "Generate Orion config for cluster-density-v2" \
  --allowedTools "Skill,Read,Write,Bash"
```

### GitHub Actions

```yaml
- uses: anthropics/claude-code@v1
  with:
    prompt: "Generate an Orion config for cluster-density-v2 on AWS"
    allowedTools: "Skill,Read,Write,Bash"
```

## Enterprise Deployment

Auto-register the marketplace for all users — no manual setup needed.

| OS | Settings path |
|----|--------------|
| macOS | `/Library/Application Support/ClaudeCode/settings.json` |
| Linux | `/etc/claude-code/settings.json` |
| Windows | `C:\Program Files\ClaudeCode\settings.json` |

```json
{
  "extraKnownMarketplaces": {
    "cb-skills": {
      "source": {
        "source": "github",
        "repo": "cloud-bulldozer/org-skills"
      }
    }
  },
  "enabledPlugins": {
    "orion@cb-skills": true
  }
}
```

Deploy with your configuration management tool (Ansible, Chef, MDM, etc.).
