---
layout: default
title: Setup — API / SDK / Other LLMs
---

# API, SDK, and Other LLMs

Skills are markdown files. Any LLM that accepts a system prompt can use them — no special integration required.

## Reading a Skill

```python
from pathlib import Path

skill = Path("orion/skills/orion-regression-analysis/SKILL.md").read_text()
```

That's it. `skill` is now a string you pass as a system prompt to any provider.

## Provider Examples

### Anthropic (Claude API)

```python
from anthropic import Anthropic

client = Anthropic()
response = client.messages.create(
    model="claude-sonnet-4-6",
    system=skill,
    max_tokens=4096,
    messages=[{
        "role": "user",
        "content": "Build an Orion config for cluster-density-v2 on AWS with 24 workers"
    }]
)
```

### OpenAI (GPT-4o, o3)

```python
import openai

response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": skill},
        {"role": "user", "content": "Build an Orion config for cluster-density-v2 on AWS"}
    ]
)
```

### Google Gemini

```python
import google.generativeai as genai

model = genai.GenerativeModel("gemini-2.5-pro", system_instruction=skill)
response = model.generate_content("Build an Orion config for node-density")
```

### Ollama (Local Models)

```python
import openai

client = openai.OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
response = client.chat.completions.create(
    model="llama3.1",
    messages=[
        {"role": "system", "content": skill},
        {"role": "user", "content": "Build an Orion config for cluster-density-v2"}
    ]
)
```

### Claude Agent SDK (TypeScript)

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const msg of query({
  prompt: "Build an Orion config for cluster-density-v2 on AWS",
  options: {
    cwd: "/path/to/project",
    settingSources: ["user", "project"],
    allowedTools: ["Skill", "Read", "Write", "Bash"],
    permissionMode: "dontAsk"
  }
})) {
  console.log(msg);
}
```

## Compatibility

| Provider | How to Use | Notes |
|----------|-----------|-------|
| **Claude Code** | Native plugin (`/orion-regression-analysis`) | Auto-triggers on context |
| **Claude API** | `system` parameter | Full markdown support |
| **OpenAI** | `system` role message | Works with GPT-4o, o3 |
| **Gemini** | `system_instruction` | Works with 2.5 Pro/Flash |
| **Ollama** | `system` role via OpenAI-compat API | Any local model |
| **Cursor** | `@file:` reference or `.cursorrules` | Via flat skills directory |
| **Agent SDK** | `settingSources` loads from filesystem | Python and TypeScript |
