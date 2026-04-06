# Orion Troubleshooting Guide

This guide helps you diagnose and resolve common issues when using Orion for performance regression detection.

## Quick Reference: Common Issues

| Error Message | Likely Cause | Solution |
|---------------|--------------|----------|
| "No UUID present for given metadata" | Wrong benchmark name | Query ES for available benchmarks (see below) |
| "Connection refused" | Wrong ES URL or network issue | Validate ES config, check network |
| "Authentication failed" | Wrong credentials | Update credentials in ES config |
| "No data found" | Wrong filters or date range | Check metadata filters, expand lookback |
| "Metric field not found" | Wrong metric name | Verify field exists in ES schema |

## Common Issues and Solutions

### No Data Found

**Symptoms:**
- "No data found" error messages
- Empty results with no metrics
- Zero test runs matched

**Diagnosis Steps:**

1. **Check Elasticsearch connectivity:**
   ```bash
   curl -X GET "https://your-opensearch.com/_cluster/health"
   ```

2. **Verify index existence:**
   ```bash
   curl -X GET "https://your-opensearch.com/_cat/indices/ripsaw*"
   curl -X GET "https://your-opensearch.com/_cat/indices/perf_scale*"
   ```

3. **Test basic query:**
   ```bash
   curl -X POST "https://your-opensearch.com/your-index/_search" \
     -H 'Content-Type: application/json' \
     -d '{"query": {"match_all": {}}, "size": 1}'
   ```

**Common Fixes:**

**Wrong Index Names:**
```yaml
# Check actual index names in your cluster
--benchmark-index=ripsaw-kube-burner-*    # vs ripsaw-*
--metadata-index=perf_scale_ci*           # vs perf-scale-*
```

**Metadata Filters Too Restrictive:**
```yaml
metadata:
  platform: AWS
  ocpVersion: "4.22"
  # Remove filters one by one to find the issue
```

**Field Name Mismatches:**
```bash
# Use debug mode to see generated queries
orion --config config.yaml --debug --lookback=1d
```

**Time Range Issues:**
```bash
# Try shorter lookback periods
--lookback=7d    # instead of 30d
--lookback=1d    # for quick testing
```

### Configuration Errors

**Symptoms:**
- YAML parsing errors
- Invalid configuration warnings
- Unexpected metric behavior

**Common Configuration Issues:**

**YAML Syntax Errors:**
```yaml
# Bad: Missing quotes around version
ocpVersion: 4.22

# Good: Quoted version
ocpVersion: "4.22"

# Bad: Invalid indentation
metrics:
- name: test
  metricName: value

# Good: Proper indentation
metrics:
  - name: test
    metricName: value
```

**Field Name Issues:**
```yaml
# Check if field names exist in your ES index
# Bad: Wrong field name
metricName: containerCPU_wrong

# Good: Correct field name (check your ES schema)
metricName: containerCPU
```

**Template Variable Issues:**
```yaml
# Bad: Undefined variable
ocpVersion: "{{ undefined_var }}"

# Good: Variable with default
ocpVersion: "{{ version | default('4.22') }}"

# Run with variables defined
orion --config config.yaml --input-vars='{"version": "4.22"}'
```

### Poor Regression Detection

**Symptoms:**
- No regressions detected when expected
- Too many false positives
- Inconsistent detection results

**Tuning Strategies:**

**Threshold Too High:**
```yaml
# If missing regressions, lower thresholds
threshold: 5    # instead of 20
```

**Threshold Too Low:**
```yaml
# If too many false positives, raise thresholds
threshold: 25   # instead of 5
```

**Wrong Direction:**
```yaml
# For latency metrics (increases are bad)
direction: 1

# For throughput metrics (decreases are bad)  
direction: -1

# For debugging, detect both
direction: 0
```

**Missing Aggregation:**
```yaml
# Bad: Missing aggregation for multi-value metric
- name: cpuUsage
  metricName: containerCPU
  metric_of_interest: value

# Good: Add aggregation
- name: cpuUsage
  metricName: containerCPU
  metric_of_interest: value
  agg:
    value: cpu
    agg_type: avg
```

**Correlation Issues:**
```yaml
# Bad: Correlation prevents detection
- name: podLatency
  correlation: nonexistent_metric_avg

# Good: Valid correlation or remove it
- name: podLatency
  correlation: apiserverCPU_avg
```

### Algorithm Selection Issues

**Hunter Analyze Not Working:**
```bash
# Try different algorithms
orion --config config.yaml --cmr              # Simple comparison
orion --config config.yaml --anomaly-detection # ML-based
```

**Anomaly Detection Tuning:**
```bash
# Adjust anomaly detection parameters
orion --config config.yaml --anomaly-detection \
  --anomaly-window=10 \
  --min-anomaly-percent=15
```

### Performance Issues

**Symptoms:**
- Slow query execution
- Timeout errors
- Large memory usage

**Optimization Strategies:**

**Reduce Query Scope:**
```bash
# Use shorter time ranges
--lookback=7d    # instead of 30d

# Use smaller result sets
--lookback-size=5000    # instead of 10000
```

**Optimize Metadata Filters:**
```yaml
# Add more specific filters
metadata:
  platform: AWS
  benchmark.keyword: cluster-density-v2
  # More specific = faster queries
```

**Use Targeted Metrics:**
```yaml
# Remove noisy or unnecessary metrics
metrics:
  # Keep only essential metrics for initial analysis
  - name: podReadyLatency
    # ... essential metric config
```

## Debugging Techniques

### Enable Debug Logging

```bash
orion --config config.yaml --debug --lookback=1d
```

Debug output shows:
- Generated Elasticsearch queries
- Data processing steps
- Metric calculation details
- Correlation analysis

### Validate Configuration

**Check YAML syntax:**
```bash
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

**Test with minimal config:**
```yaml
tests:
  - name: debug-test
    metadata:
      platform: AWS    # Start with single filter
    metrics:
      - name: simple-metric
        metricName: simple_field
        metric_of_interest: value
        # Minimal metric for testing
```

### Incremental Development

1. **Start Simple:**
   ```yaml
   # Minimal working config
   metadata:
     benchmark.keyword: cluster-density-v2
   metrics:
     - name: test
       metricName: podLatencyQuantilesMeasurement
       metric_of_interest: P99
   ```

2. **Add Filters Gradually:**
   ```yaml
   # Add one filter at a time
   metadata:
     benchmark.keyword: cluster-density-v2
     platform: AWS  # <- Add this
   ```

3. **Test Each Addition:**
   ```bash
   orion --config config.yaml --debug --lookback=1d
   ```

### Query Analysis

**Check Generated Queries:**
1. Run with `--debug`
2. Look for Elasticsearch query JSON in output
3. Test query directly against Elasticsearch
4. Verify field names and values match your data

**Example debug output analysis:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"platform": "AWS"}},
        {"term": {"benchmark.keyword": "cluster-density-v2"}}
      ]
    }
  }
}
```

### Data Validation

**Check Data Structure:**
```bash
# Get sample document
curl -X POST "https://your-es.com/your-index/_search" \
  -H 'Content-Type: application/json' \
  -d '{"query": {"match_all": {}}, "size": 1}'
```

**Verify Field Types:**
```bash
# Get index mapping
curl -X GET "https://your-es.com/your-index/_mapping"
```

## Error Message Reference

### "Invalid algorithm called"
- **Cause:** Misspelled algorithm option
- **Fix:** Use `--hunter-analyze`, `--cmr`, or `--anomaly-detection`

### "metadata-index and es-server flags must be provided"
- **Cause:** Missing required command line arguments
- **Fix:** Add `--es-server` and `--metadata-index` flags

### "No matching ACK entries found"
- **Cause:** ACK file doesn't match current test criteria
- **Fix:** Check ACK file filters or use `--no-default-ack`

### "Correlation metric not found"
- **Cause:** Referenced metric in correlation doesn't exist
- **Fix:** Check metric names and aggregation types in correlation

### "Template variable not found"
- **Cause:** Jinja2 template variable not provided
- **Fix:** Add variable to `--input-vars` or provide default

## Best Practices for Troubleshooting

### Systematic Approach

1. **Verify Environment:**
   - Check ES connectivity
   - Validate index names
   - Confirm data availability

2. **Test Configuration:**
   - Start with minimal config
   - Add complexity gradually
   - Test each change

3. **Analyze Results:**
   - Use debug logging
   - Check generated queries
   - Verify data matches expectations

### Development Workflow

```bash
# 1. Test connectivity
curl -X GET "https://your-es.com/_cluster/health"

# 2. Test minimal config
orion --config minimal.yaml --debug --lookback=1d

# 3. Add complexity incrementally
orion --config full.yaml --debug --lookback=1d

# 4. Production run
orion --config full.yaml --lookback=15d --viz
```

### Logging Strategy

**Development:**
```bash
--debug    # Full debug output
```

**Production:**
```bash
# Normal logging (INFO level)
# Redirect to file for later analysis
orion --config config.yaml > analysis.log 2>&1
```

### Configuration Management

**Version Control:**
- Keep configurations in git
- Use meaningful commit messages
- Tag working configurations

**Testing:**
- Test configurations with recent data
- Validate on different time ranges
- Compare results across algorithm types

**Documentation:**
- Document threshold tuning decisions
- Note correlation rationale
- Record debugging findings

Remember: Effective troubleshooting requires understanding both your data structure and Orion's configuration patterns. When in doubt, start simple and build complexity gradually.
## Finding the Correct Benchmark Name

### Problem
Orion returns "No UUID present for given metadata" - this means no test runs match your `benchmark.keyword` value.

### Solution: Query Elasticsearch for Available Benchmarks

Use this command to see all available benchmarks in your ES cluster:

```bash
curl -s -u "username:password" \
  "https://your-es-server.com/perf_scale_ci*/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "aggs": {
      "benchmarks": {
        "terms": {
          "field": "benchmark.keyword",
          "size": 100
        }
      }
    }
  }' | python3 -c "import sys, json; \
    data = json.load(sys.stdin); \
    benchmarks = data['aggregations']['benchmarks']['buckets']; \
    print('\nAvailable Benchmarks:'); \
    print('='*60); \
    for b in benchmarks: \
      print(f'{b[\"key\"]:40} {b[\"doc_count\"]:>6} runs')"
```

### Common Benchmark Names

**Density Tests**:
- `cluster-density-v2` - Control plane stress with high pod count
- `node-density` - Node capacity with max pods per node
- `node-density-cni` - Node density with CNI focus
- `node-density-heavy` - Heavy workload node density
- `udn-density-pods` - User-defined network density

**Specialized Tests**:
- `network-policy` - Network policy performance
- `ingress-perf` - Ingress controller performance
- `workers-scale` - Worker node scaling
- `virt-density` - Virtualization workload density

**Other**:
- `olm` - Operator Lifecycle Manager performance
- `crd-scale` - CRD scaling tests
- `k8s-netperf` - Kubernetes network performance

### Filter by OCP Version

To see benchmarks for a specific version:

```bash
curl -s -u "username:password" \
  "https://your-es-server.com/perf_scale_ci*/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "query": {
      "prefix": {
        "ocpVersion": "4.22"
      }
    },
    "aggs": {
      "benchmarks": {
        "terms": {
          "field": "benchmark.keyword",
          "size": 50
        }
      }
    }
  }' | python3 -c "import sys, json; \
    data = json.load(sys.stdin); \
    print('\n'.join([f'{b[\"key\"]:40} ({b[\"doc_count\"]} runs)' \
    for b in data['aggregations']['benchmarks']['buckets']]))"
```

### Tips

1. **Exact match required**: `benchmark.keyword` is case-sensitive
2. **Check for variations**: `udn-density` vs `udn-density-pods`
3. **Look at run counts**: Low run counts may not have enough data for analysis
4. **Version-specific**: Some benchmarks only exist in certain OCP versions

