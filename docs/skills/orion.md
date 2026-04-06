---
layout: default
title: Skills — Orion
---

# Orion

**Plugin:** `orion` | **Version:** 1.0.0 | **Source:** [jtaleric/orion-skill](https://github.com/jtaleric/orion-skill)

[Orion](https://github.com/cloud-bulldozer/orion) is a CLI tool that detects performance regressions in OpenShift benchmark data stored in Elasticsearch/OpenSearch. This skill turns your AI assistant into an Orion expert.

## Skill: orion-regression-analysis

An interactive assistant that guides you through the full Orion workflow:

1. **Elasticsearch setup** — connect to your ES/OpenSearch cluster, validate credentials, configure index patterns
2. **Metric discovery** — explore available benchmarks, metrics, namespaces, node configurations, and OCP versions in your data
3. **Config generation** — build valid Orion YAML configs with correct metadata filters, metric definitions, aggregations, and thresholds
4. **Regression detection** — choose the right algorithm (hunter-analyze, anomaly-detection, CMR), run analysis, interpret results
5. **Troubleshooting** — debug connection issues, fix config errors, tune detection sensitivity

### Triggers

The skill auto-activates when you mention:
- "Orion config", "build an Orion config", "Orion YAML"
- "performance regression", "OpenShift performance"
- Discovering metrics for benchmarks

### Supported Benchmarks

| Type | Benchmarks | Index Pattern |
|------|-----------|---------------|
| **kube-burner** | cluster-density-v2, node-density, node-density-cni, node-density-heavy, workers-scale, crd-scale, network-policy, and more | `ripsaw-kube-burner-*` |
| **k8s-netperf** | TCP_STREAM, UDP_STREAM, TCP_RR, TCP_CRR profiles | `k8s-netperf` |

### Included Resources

The skill ships with reference docs, utility scripts, and example configs:

**Guides (`docs/`):**

| File | Purpose |
|------|---------|
| `config-building-guide.md` | YAML structure, metadata filters, metric definitions, inheritance |
| `kube-burner-patterns.md` | Control plane, node-level, and application metric patterns |
| `k8s-netperf-patterns.md` | Network performance config patterns and common mistakes |
| `elasticsearch-asset-setup.md` | ES/OpenSearch connection setup and security |
| `discovery-quick-reference.md` | Quick reference for the discovery script |
| `troubleshooting.md` | Common issues and debugging steps |
| `claude-workflow-guide.md` | Interaction patterns for the AI assistant |
| `aggregation-structure.md` | `agg:` field structure and types |
| `node-config-metadata.md` | Why and how to include node configuration in metadata |
| `FIELD-PRIORITY-SUMMARY.md` | Smart field fallback logic for discovery |

**Examples (`docs/examples/`):**

| File | What It Demonstrates |
|------|---------------------|
| `basic-cluster-density.yaml` | Control plane analysis — API server, etcd, OVN CPU |
| `node-density.yaml` | Node-level analysis — kubelet, CRI-O, OVS, pod scheduling |
| `k8s-netperf.yaml` | Network performance — TCP/UDP throughput and latency |
| `inheritance-example.yaml` | Config reuse with `parentConfig` and `metricsFile` |

**Scripts (`scripts/`):**

| Script | Purpose |
|--------|---------|
| `discover-es-data.py` | Explore ES data — benchmarks, metrics, namespaces, platforms, versions, node configs |
| `validate-es-asset.py` | Validate ES connection, credentials, and index accessibility |

### Example Usage

```
> Help me create an Orion config for cluster-density-v2 on AWS with 3 master and 24 worker m6a.xlarge nodes

> What benchmarks are available in my Elasticsearch data?

> I'm seeing etcd latency regressions on OCP 4.17 — help me investigate

> Build a k8s-netperf config for TCP_STREAM and TCP_RR on pod network
```
