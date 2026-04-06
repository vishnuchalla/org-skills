# Smart Field Priority - Implementation Summary

## The Problem

Different Elasticsearch indexes use different field names for benchmark identifiers:
- **Metadata index** (`perf_scale_ci*`) uses `benchmark.keyword` or `benchmark`
- **Benchmark/data indexes** (`ripsaw-kube-burner-*`, `k8s-netperf`) use `jobName`

Previously, the discovery script would try fields in a fixed order, leading to inefficient queries.

## The Solution: `get_benchmark_field_priority(index)`

This function analyzes the index pattern and returns the optimal field order:

```python
def get_benchmark_field_priority(index):
    """
    Determine field priority based on index pattern.

    Metadata indexes (perf_scale_ci*) use benchmark.keyword
    Benchmark/data indexes (ripsaw-kube-burner-*, k8s-netperf-*) use jobName
    """
    index_lower = index.lower()

    # Check if this is a metadata index
    if 'perf_scale_ci' in index_lower or 'metadata' in index_lower:
        # Metadata index - benchmark fields first
        return [
            ("benchmark.keyword", "benchmark.keyword"),
            ("benchmark", "benchmark"),
            ("jobName", "jobName")
        ]
    else:
        # Benchmark/data index - jobName first
        return [
            ("jobName", "jobName"),
            ("benchmark.keyword", "benchmark.keyword"),
            ("benchmark", "benchmark")
        ]
```

## Functions Using Smart Priority

All 4 benchmark-filtering functions now use smart field priority:

### 1. `discover_benchmarks(es, index)`
- Uses: `get_benchmark_field_priority(index)`
- Shows: `🎯 Field priority: jobName → benchmark.keyword → benchmark`
- Shows: `🔑 Using field: jobName`

### 2. `discover_metrics(es, index, benchmark)`
- Uses: `get_benchmark_field_priority(index)`
- Shows: `🎯 Field priority: jobName → benchmark.keyword → benchmark`
- Shows: `🔑 Using field: jobName`

### 3. `discover_versions(es, index, benchmark=None)`
- Uses: `get_benchmark_field_priority(index)` when filtering by benchmark
- Tries all field patterns in priority order

### 4. `sample_document(es, index, benchmark=None, profile=None)`
- Uses: `get_benchmark_field_priority(index)` when filtering by benchmark
- Shows: `🎯 Field priority: jobName → benchmark.keyword → benchmark`
- Shows: `🔑 Using field: jobName`

## Expected Behavior

### Querying Metadata Index (perf_scale_ci*)

```bash
$ python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml benchmarks

✓ Connected to: https://...
📊 Using metadata index: perf_scale_ci*

🔍 Searching index: perf_scale_ci*
📊 Total documents: 5,234
🎯 Field priority: benchmark.keyword → benchmark → jobName    ← benchmark.keyword FIRST
🔑 Using field: benchmark.keyword                             ← Found it!

Available Benchmarks:
======================================================================
cluster-density-v2                                      1,234 runs
```

### Querying Benchmark Index (ripsaw-kube-burner-*)

```bash
$ python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml metrics --benchmark cluster-density-v2

✓ Connected to: https://...
📈 Using benchmark index: ripsaw-kube-burner-*

🔍 Searching index: ripsaw-kube-burner-*
📊 Documents for benchmark 'cluster-density-v2': 15,432
🎯 Field priority: jobName → benchmark.keyword → benchmark    ← jobName FIRST!
🔑 Using field: jobName                                       ← Found it!

Available Metrics:
======================================================================
containerCPU                                                12,345
```

### Sample Document with Smart Priority

```bash
$ python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml sample --benchmark cluster-density-v2

✓ Connected to: https://...
📈 Using benchmark index: ripsaw-kube-burner-*

🔍 Searching index: ripsaw-kube-burner-*
🎯 Field priority: jobName → benchmark.keyword → benchmark    ← Shows what will be tried
🔑 Using field: jobName                                       ← Shows what worked!
   Filters: jobName='cluster-density-v2'

📄 Sample Document Structure:
======================================================================
{
  "jobName": "cluster-density-v2",
  "metricName": "containerCPU",
  ...
}
```

## Field Priority by Index

| Index Pattern | 1st Priority | 2nd Priority | 3rd Priority | Rationale |
|---------------|--------------|--------------|--------------|-----------|
| `perf_scale_ci*` | `benchmark.keyword` | `benchmark` | `jobName` | Metadata uses benchmark |
| `ripsaw-kube-burner-*` | `jobName` | `benchmark.keyword` | `benchmark` | Data uses jobName |
| `k8s-netperf` | `jobName` | `benchmark.keyword` | `benchmark` | Data uses jobName |
| Other | `jobName` | `benchmark.keyword` | `benchmark` | Default to data pattern |

## Test Commands

Verify the smart priority is working:

```bash
# Test metadata index (should use benchmark.keyword first)
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml benchmarks

# Test benchmark index (should use jobName first)
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml metrics --benchmark cluster-density-v2

# Test sample with benchmark filter (should use jobName first for ripsaw-kube-burner-*)
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml sample --benchmark cluster-density-v2

# Test k8s-netperf (should use jobName first)
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml --index k8s-netperf sample
```

## Benefits

✅ **Efficient**: Tries the most likely field first based on index type
✅ **Transparent**: Shows exactly which fields are being tried in what order
✅ **Robust**: Still falls back to other fields if primary doesn't exist
✅ **Consistent**: All discovery functions use the same smart priority logic
✅ **Educational**: Users can see why certain fields are prioritized

## Files Modified

- `scripts/discover-es-data.py` - Added `get_benchmark_field_priority()` function
- `scripts/discover-es-data.py` - Updated 4 discovery functions to use smart priority
- `docs/discovery-quick-reference.md` - Documented smart field priority
- `SKILL.md` - Updated discovery section with field priority notes
