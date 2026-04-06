# Discovery Script Quick Reference

## Critical Syntax Rule

⚠️ **The `--config` flag MUST come BEFORE the subcommand!**

```bash
# ✅ CORRECT
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml benchmarks

# ❌ WRONG
python3 scripts/discover-es-data.py benchmarks --config ~/.orion/elasticsearch-config.yaml
```

## Automatic Index Selection

🎯 **The script automatically uses the correct index based on what you're discovering!**

| Command | Index Used | Reason |
|---------|------------|--------|
| `benchmarks` | **metadata_index** | Benchmark names stored in metadata |
| `platforms` | **metadata_index** | Platform info stored in metadata |
| `versions` | **metadata_index** | OCP versions stored in metadata |
| `node-config` | **metadata_index** | Node configuration stored in metadata |
| `metrics` | **benchmark_index** | Metric data in kube-burner index |
| `namespaces` | **benchmark_index** | Namespace labels in metric data |
| `sample` | **benchmark_index** | Usually sampling metric data |
| `profiles` | **benchmark_index** | k8s-netperf test profiles |
| `scenarios` | **benchmark_index** | k8s-netperf test scenarios |

**Override when needed:**
- Use `--index k8s-netperf` for network performance data (single index, not a pattern)
- Use `--use-benchmark-index` to force benchmark_index (for debugging)

**Index Patterns:**
- `perf_scale_ci*` - Metadata index (uses wildcard pattern)
- `ripsaw-kube-burner-*` - Benchmark/data index (uses wildcard pattern)
- `k8s-netperf` - Network performance index (**single index**, no wildcard)

Example:
```bash
# Automatically uses metadata_index (perf_scale_ci*)
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml benchmarks

# Automatically uses benchmark_index (ripsaw-kube-burner-*)
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml metrics --benchmark cluster-density-v2

# Override to use k8s-netperf index (single index)
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml --index k8s-netperf profiles
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml --index k8s-netperf benchmarks
```

## Smart Multi-Field Support

🔑 **The script intelligently tries benchmark fields based on index type!**

Different indexes use different field names:
- **Metadata indexes** (`perf_scale_ci*`): typically use `benchmark.keyword` or `benchmark`
- **Benchmark/data indexes** (`ripsaw-kube-burner-*`): typically use `jobName`

The script **automatically adjusts field priority** based on which index you're querying:

### Metadata Index (perf_scale_ci*)
Field priority: `benchmark.keyword` → `benchmark` → `jobName`

### Benchmark Index (ripsaw-kube-burner-*)
Field priority: `jobName` → `benchmark.keyword` → `benchmark`

### k8s-netperf Index (k8s-netperf)
- **Index name**: `k8s-netperf` (single index, not a wildcard pattern)
- **Field priority**: `jobName` → `benchmark.keyword` → `benchmark` (treated as data index)
- **Contains**: Both metadata and result data in one index
- **Usage**: Always specify `--index k8s-netperf` when discovering network performance data

This means:
1. When discovering benchmarks from metadata → tries `benchmark.keyword` first
2. When discovering metrics from data → tries `jobName` first
3. Always shows field order tried: 🎯 Field priority: jobName → benchmark.keyword → benchmark
4. Shows which field worked: 🔑 Using field: jobName

This applies to all discovery commands that filter by benchmark:
- `benchmarks` - smart field priority based on index
- `metrics --benchmark <name>` - smart field priority based on index
- `versions --benchmark <name>` - smart field priority based on index
- `sample --benchmark <name>` - smart field priority based on index

### Example Output

```bash
$ python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml benchmarks

✓ Connected to: https://your-es.com
📊 Using metadata index: perf_scale_ci*

🔍 Searching index: perf_scale_ci*
📊 Total documents: 5,234
🎯 Field priority: benchmark.keyword → benchmark → jobName    ← Shows order tried
🔑 Using field: benchmark.keyword                             ← Shows which worked

Available Benchmarks:
======================================================================
cluster-density-v2                                      1,234 runs
```

```bash
$ python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml metrics --benchmark cluster-density-v2

✓ Connected to: https://your-es.com
📈 Using benchmark index: ripsaw-kube-burner-*

🔍 Searching index: ripsaw-kube-burner-*
📊 Documents for benchmark 'cluster-density-v2': 15,432
🎯 Field priority: jobName → benchmark.keyword → benchmark    ← jobName first for data!
🔑 Using field: jobName                                       ← Found via jobName

Available Metrics:
======================================================================
containerCPU                                                12,345
```

## Common Commands

All commands should be run from the skill directory:

```bash
cd ~/.claude/skills/orion-regression-analysis
```

### 1. Discover Benchmarks
```bash
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml benchmarks
```

Shows:
- ✓ Connection status
- 📊 Total documents in index
- List of benchmarks with run counts
- ⚠️ Helpful errors if no data found

### 2. Discover Metrics
```bash
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml metrics --benchmark cluster-density-v2
```

Shows:
- Available metricName values for the benchmark
- Document counts for each metric
- Warnings if benchmark not found

### 3. Discover Namespaces
```bash
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml namespaces --metric containerCPU
```

Shows:
- Namespaces where the metric appears
- Sample counts per namespace

### 4. Get Sample Document
```bash
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml sample --benchmark cluster-density-v2
```

Shows:
- Full JSON structure of a sample document
- Useful for understanding field names and structure

### 5. Discover Platforms
```bash
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml platforms
```

Shows:
- Available platforms (AWS, GCP, Azure, etc.)
- Run counts per platform

### 6. Discover Node Configuration
```bash
# All benchmarks
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml node-config

# Specific benchmark only (recommended)
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml node-config --benchmark cluster-density-v2
```

Shows:
- **Node counts** (master, worker, infra) - how many nodes per run
- **Instance types** (m5.xlarge, m6a.2xlarge, etc.) - what instance types are used
- **🔗 Count + Type Correlations** - which instance types are used with each node count
  - Example: "6 × m6a.xlarge (371 runs)" means 6-worker configs using m6a.xlarge
  - Helps you choose the correct combination for your config
- **Automatically skips instance types for baremetal platforms**
- **Optional --benchmark filter** to isolate results for a specific test

Example output (filtered by benchmark):
```
🔍 Searching index: perf_scale_ci*
🎯 Field priority: benchmark.keyword → benchmark → jobName
📌 Filtering by benchmark: cluster-density-v2
🔑 Using field: benchmark.keyword
📊 Total runs for 'cluster-density-v2': 871

📊 Platforms found: AWS, GCP

🔢 Node Counts:
======================================================================
  masterNodesCount         3 (859 runs), 5 (3 runs)
  workerNodesCount         3 (279 runs), 6 (371 runs), 24 (90 runs), 120 (63 runs)

🖥️  Instance Types:
======================================================================
  masterNodesType.keyword  m6a.xlarge (646 runs), m6a.4xlarge (115 runs)
  workerNodesType.keyword  m6a.xlarge (632 runs), m5.xlarge (90 runs)

🔗 Count + Type Correlations:
======================================================================

  Worker Nodes:
       6 × m6a.xlarge                          ( 371 runs)  ← Most common 6-worker config
       3 × m6a.xlarge                          ( 170 runs)
      24 × m6a.xlarge                          (  69 runs)
     120 × m5.xlarge                           (  63 runs)

  Master Nodes:
       3 × m6a.xlarge                          ( 646 runs)  ← Most common master config
       3 × m6a.4xlarge                         ( 115 runs)
```

**Benefits of --benchmark filter:**
- See node configurations specific to a test type
- Understand infrastructure used for particular benchmarks
- **Correlation section shows exact count+type combinations** (e.g., "6 × m6a.xlarge")
- Pick the most common combination for your config
- Avoid mixing node configs from different test types
- More accurate when creating configs

**Note**: For baremetal platforms, instance types are not applicable and will be skipped.

### 7. Discover Versions
```bash
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml versions --benchmark cluster-density-v2
```

Shows:
- Available OCP versions
- Run counts per version

### 8. Get Sample Document
```bash
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml sample --benchmark cluster-density-v2
```

Shows:
- Full JSON structure of a sample document
- Useful for understanding field names and structure

### 9. k8s-netperf Discovery

For network performance data (uses **k8s-netperf** index):

```bash
# List test profiles
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml --index k8s-netperf profiles

# List scenarios for a profile
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml --index k8s-netperf scenarios --profile TCP_STREAM

# Discover available benchmarks/jobNames in k8s-netperf
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml --index k8s-netperf benchmarks

# Get sample k8s-netperf document
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml --index k8s-netperf sample
```

**Note:** k8s-netperf uses a **single index** named `k8s-netperf` (not a pattern like `k8s-netperf-*`). This index contains both metadata and result data together.

## Improved Output

The script now provides:

- ✓ **Connection confirmation** - Shows ES server, cluster name, version
- 📊 **Document counts** - Shows how many documents matched
- 🔑 **Field indicator** - Shows which field was used (benchmark.keyword, jobName, or benchmark)
- ⚠️ **Clear error messages** - Explains what went wrong and how to fix it
- 💡 **Suggestions** - Recommends next steps when no data found

## Troubleshooting

### "0 benchmarks found"
Check:
1. ✓ Connection status (shown in output)
2. Index pattern in elasticsearch-config.yaml
3. Data actually exists in ES
4. None of the benchmark fields exist (script tries `benchmark.keyword`, `jobName`, and `benchmark` automatically)

### "No documents found for benchmark 'X'"
- Benchmark name is case-sensitive
- Verify benchmark exists: run `benchmarks` command first
- Script automatically tries three field patterns: `benchmark.keyword`, `jobName`, and `benchmark`
- Check the output for "🔑 Using field:" to see which field was found

### "Connection failed"
- Verify credentials in elasticsearch-config.yaml
- Check network access to ES
- Run: `python3 scripts/validate-es-asset.py ~/.orion/elasticsearch-config.yaml`

## Default Config Location

If you omit `--config`, the script uses: `~/.orion/elasticsearch-config.yaml`

```bash
# These are equivalent if config is in default location
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml benchmarks
python3 scripts/discover-es-data.py benchmarks
```

## When to Use Discovery

**Always use discovery when:**
1. Creating a new Orion config
2. User asks "what data is available?"
3. Troubleshooting "field not found" errors
4. User wants to monitor a component but doesn't know metric names
5. Verifying data exists before analysis
