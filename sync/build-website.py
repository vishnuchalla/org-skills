#!/usr/bin/env python3
"""Generate docs/data.json from marketplace.json and each plugin's skill metadata."""

import json
import os
import glob as globmod

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKETPLACE = os.path.join(ROOT, ".claude-plugin", "marketplace.json")
OUTPUT = os.path.join(ROOT, "docs", "data.json")


def parse_skill_frontmatter(path):
    """Extract name, description from SKILL.md YAML frontmatter."""
    with open(path) as f:
        content = f.read()

    if not content.startswith("---"):
        return None

    end = content.index("---", 3)
    frontmatter = content[3:end]

    info = {}
    current_key = None
    for line in frontmatter.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Continuation line (indented) for multi-line values
        if line.startswith("  ") and current_key:
            info[current_key] = info.get(current_key, "") + " " + stripped
            continue
        if ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            current_key = key if key in ("name", "description") else None
            if current_key:
                # Handle block scalar indicators (>-, |-, >, |)
                if val in (">-", "|-", ">", "|"):
                    info[key] = ""
                else:
                    info[key] = val

    # Clean up whitespace
    for key in info:
        info[key] = " ".join(info[key].split())

    return info if "name" in info else None


def main():
    with open(MARKETPLACE) as f:
        marketplace = json.load(f)

    plugins = []

    for entry in sorted(marketplace["plugins"], key=lambda e: e["name"]):
        plugin_dir = os.path.join(ROOT, entry["source"])
        has_readme = os.path.exists(os.path.join(plugin_dir, "skills"))

        skills = []
        skill_paths = sorted(globmod.glob(os.path.join(plugin_dir, "skills", "*", "SKILL.md")))
        for skill_path in skill_paths:
            info = parse_skill_frontmatter(skill_path)
            if info:
                skill_id = os.path.basename(os.path.dirname(skill_path))
                skills.append({
                    "name": info.get("name", skill_id),
                    "id": skill_id,
                    "description": info.get("description", ""),
                })

        plugins.append({
            "name": entry["name"],
            "version": entry["version"],
            "description": entry["description"],
            "has_readme": has_readme,
            "commands": [],
            "skills": skills,
            "hooks": [],
        })

    data = {"plugins": plugins}

    with open(OUTPUT, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    print(f"docs/data.json generated: {len(plugins)} plugin(s)")


if __name__ == "__main__":
    main()
