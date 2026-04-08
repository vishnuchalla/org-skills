.PHONY: help build update

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build the container image
	podman build -t org-skills -f images/Dockerfile .

update: ## Regenerate PLUGINS.md, docs/data.json, and sync marketplace versions
	python3 sync/sync_marketplace_versions.py
	python3 sync/generate_plugin_docs.py
	python3 sync/build-website.py
