# Node Configuration as Metadata Filters

## Overview

Node configuration (instance types and counts) should be included as **metadata filters** in Orion YAML configurations. This ensures you're comparing runs with similar infrastructure characteristics.

## Required Fields

When creating Orion configs, **always include** these metadata fields:

```yaml
tests:
  - name: your-test
    metadata:
      # Platform
      platform: AWS
      
      # Node configuration - REQUIRED for accurate analysis
      masterNodesType: m6a.xlarge
      masterNodesCount: 3
      workerNodesType: m6a.xlarge
      workerNodesCount: 6
      
      # Test identification
      benchmark.keyword: cluster-density-v2
      ocpVersion: "{{ version }}"
```

## Why Include Node Configuration?

### 1. **Infrastructure Consistency**
Comparing performance across different instance types or node counts can lead to false positives:

❌ **Bad**: Comparing 6 workers vs 24 workers
- Different resource availability
- Different scheduling patterns
- Not a fair comparison

✅ **Good**: Filtering to only 6 workers
- Consistent infrastructure
- Fair performance comparison
- Accurate regression detection

### 2. **Resource Capacity Matters**
Different instance types have different performance characteristics:

❌ **Bad**: Mixing m5.xlarge and m6i.4xlarge
- Different CPU generations
- Different memory/CPU ratios
- Performance differences are infrastructure, not regressions

✅ **Good**: Filtering to m6a.xlarge only
- Consistent hardware profile
- Performance changes are real regressions
- Apples-to-apples comparison

### 3. **Test Accuracy**
Node density tests are especially sensitive to node configuration:

```yaml
# Node density with 12 workers
workerNodesCount: 12
# vs
# Node density with 6 workers  
workerNodesCount: 6

# These are COMPLETELY different tests!
# Must filter to specific count for accurate analysis
```

## Discovery Workflow

Use the `node-config` discovery command to find appropriate values:

```bash
# Step 1: Discover what node configs exist for your benchmark
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml \
  node-config --benchmark cluster-density-v2

# Output shows:
# 🔢 Node Counts:
#   masterNodesCount: 3 (859 runs)
#   workerNodesCount: 6 (371 runs), 3 (279 runs), 24 (90 runs)
# 🖥️  Instance Types:
#   masterNodesType.keyword: m6a.xlarge (646 runs), m6a.4xlarge (115 runs)
#   workerNodesType.keyword: m6a.xlarge (632 runs), m5.xlarge (90 runs)
# 🔗 Count + Type Correlations:
#   Worker Nodes:
#       6 × m6a.xlarge                          ( 371 runs)  ← Most common 6-worker config
#       3 × m6a.xlarge                          ( 170 runs)
#   Master Nodes:
#       3 × m6a.xlarge                          ( 646 runs)  ← Most common master config

# Step 2: Pick the most common combination from the correlations
# In this example: 3 masters × m6a.xlarge (646 runs), 6 workers × m6a.xlarge (371 runs)

# Step 3: Add to your config
```

## Field Names

### Standard Fields (Most Common)

```yaml
masterNodesType: m6a.xlarge      # Master node instance type
masterNodesCount: 3              # Number of master nodes
workerNodesType: m6a.xlarge      # Worker node instance type
workerNodesCount: 6              # Number of worker nodes
infraNodesType: m6a.large        # Infrastructure node type (if applicable)
infraNodesCount: 3               # Number of infra nodes (if applicable)
```

### Alternative Field Names (Some Data Sources)

```yaml
masterInstanceType: m6a.xlarge   # Alternative to masterNodesType
workerInstanceType: m6a.xlarge   # Alternative to workerNodesType
```

The discovery script checks both patterns.

## Platform-Specific Notes

### Cloud Platforms (AWS, GCP, Azure)

**Always include instance types:**

```yaml
metadata:
  platform: AWS
  masterNodesType: m6a.xlarge    # ✅ Include this
  masterNodesCount: 3            # ✅ Include this
  workerNodesType: m6a.xlarge    # ✅ Include this
  workerNodesCount: 6            # ✅ Include this
```

### Baremetal Platforms

**Skip instance types (not applicable):**

```yaml
metadata:
  platform: BareMetal
  masterNodesCount: 3            # ✅ Include counts
  workerNodesCount: 6            # ✅ Include counts
  # NO instance types for baremetal
```

The discovery script automatically detects baremetal and skips instance type queries.

## Common Patterns by Benchmark

### cluster-density-v2 (Control Plane Focus)

Typical configuration:
```yaml
metadata:
  benchmark.keyword: cluster-density-v2
  masterNodesType: m6a.xlarge
  masterNodesCount: 3
  workerNodesType: m6a.xlarge
  workerNodesCount: 6
```

**Why**: Control plane tests need consistent master resources. Worker count affects API server load.

### node-density (Node Focus)

Typical configuration:
```yaml
metadata:
  benchmark.keyword: node-density
  masterNodesType: m6a.xlarge
  masterNodesCount: 3
  workerNodesType: m6a.2xlarge    # Often larger workers
  workerNodesCount: 12             # Often more workers
```

**Why**: Node density specifically tests worker node performance. Different worker counts = different tests.

### network-performance

Typical configuration:
```yaml
metadata:
  benchmark.keyword: network-perf
  masterNodesType: m6a.xlarge
  masterNodesCount: 3
  workerNodesType: m6a.2xlarge
  workerNodesCount: 6
```

**Why**: Network performance can vary significantly by instance type (network bandwidth varies).

## Example: Complete Configuration

```yaml
tests:
  - name: cluster-density-aws-standard
    metadata:
      # Platform
      platform: AWS
      clusterType: self-managed
      networkType: OVNKubernetes

      # Node configuration (from: node-config --benchmark cluster-density-v2)
      masterNodesType: m6a.xlarge
      masterNodesCount: 3
      workerNodesType: m6a.xlarge
      workerNodesCount: 6

      # Test identification
      benchmark.keyword: cluster-density-v2
      ocpVersion: "{{ version }}"

      # Exclusions
      not:
        stream: okd

    metrics:
      - name: podReadyLatency
        threshold: 10
        metricName: podLatencyQuantilesMeasurement
        quantileName: Ready
        metric_of_interest: P99
        direction: 1
```

## Best Practices

1. **Always discover first**: Use `node-config --benchmark <name>` before creating configs
2. **Use most common configs**: Pick the configuration with the most runs
3. **Be specific**: Don't leave out node configuration - it matters!
4. **Match your analysis**: If analyzing 6-worker tests, filter to `workerNodesCount: 6`
5. **Document your choice**: Add comments explaining why you chose specific values

## Anti-Patterns to Avoid

❌ **Don't mix configurations:**
```yaml
# BAD - no node count filter
metadata:
  benchmark.keyword: cluster-density-v2
  # Missing workerNodesCount - will compare 6 vs 12 vs 24 workers!
```

❌ **Don't ignore instance types:**
```yaml
# BAD - no instance type filter  
metadata:
  platform: AWS
  workerNodesCount: 6
  # Missing workerNodesType - will compare m5 vs m6 vs m6i!
```

❌ **Don't guess values:**
```yaml
# BAD - guessed values
masterNodesCount: 3    # Did you check if this exists?
workerNodesCount: 10   # Is 10 workers even in your data?
```

✅ **Always use discovered values:**
```bash
# GOOD - discover first, then use actual values from your data
python3 scripts/discover-es-data.py node-config --benchmark cluster-density-v2
# Then use the values you see in the output
```

## Summary

- Node configuration = metadata filters
- Always include: `masterNodesType`, `masterNodesCount`, `workerNodesType`, `workerNodesCount`
- Use `node-config --benchmark <name>` to discover appropriate values
- Match your infrastructure to ensure fair comparisons
- Skip instance types for baremetal (counts only)
