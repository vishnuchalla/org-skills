# Orion Claude Skill

A comprehensive Claude Code skill for expert assistance with [Orion](https://github.com/cloud-bulldozer/orion), a CLI tool for detecting performance regressions in OpenShift perf-scale CPT runs.

This Skill will help users unfamiliar with Orion build a proper config and discover the metrics the OpenShift Performance and Scale Team collects!

## What This Skill Provides

This skill transforms Claude into an expert Orion assistant that can help you with:

- **OpenSearch Config Creation and validation**: Will help walk the user through connecting to their data warehouse.
- **Configuration Creation & Tuning**: Design YAML configs, set thresholds, configure correlations
- **Troubleshooting**: Diagnose configuration issues, query problems, and detection failures

## Usage

Once installed, you can invoke the skill in Claude Code:

### Manual Invocation
```
/orion-regression-analysis
```

### Automatic Invocation
The skill will automatically activate when you:
- Mention Orion performance analysis
- Ask about regression detection
- Work with performance configuration files
- Discuss OpenShift performance metrics

### Example Interactions

**Configuration Help:**
> "I need to create an Orion config for analyzing API server performance during cluster density tests"

**Result Interpretation:**
> "Can you help me understand these Orion regression results? I'm seeing changepoints in etcd latency"

**Troubleshooting:**
> "My Orion analysis isn't finding any data. The config looks correct but ES queries return empty results"

## Key Features

### Configuration Mastery
- YAML structure and validation
- Metadata filtering for Elasticsearch queries
- Metric aggregations and thresholds
- Correlation analysis between components
- Configuration inheritance patterns

## License

This project is licensed under the same terms as the Orion project - see the [LICENSE](LICENSE) file for details.
