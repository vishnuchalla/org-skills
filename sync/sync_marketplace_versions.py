#!/usr/bin/env python3
"""Sync plugin versions from each plugin's plugin.json into the root marketplace.json."""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKETPLACE = os.path.join(ROOT, ".claude-plugin", "marketplace.json")


def main():
    with open(MARKETPLACE) as f:
        marketplace = json.load(f)

    for entry in marketplace["plugins"]:
        plugin_json = os.path.join(ROOT, entry["source"], ".claude-plugin", "plugin.json")
        if not os.path.exists(plugin_json):
            print(f"  SKIP {entry['name']}: {plugin_json} not found")
            continue

        with open(plugin_json) as f:
            plugin = json.load(f)

        if entry["version"] != plugin["version"]:
            print(f"  {entry['name']}: {entry['version']} -> {plugin['version']}")
            entry["version"] = plugin["version"]
        else:
            print(f"  {entry['name']}: {entry['version']} (up to date)")

    with open(MARKETPLACE, "w") as f:
        json.dump(marketplace, f, indent=2)
        f.write("\n")

    print("marketplace.json synced.")


if __name__ == "__main__":
    main()
