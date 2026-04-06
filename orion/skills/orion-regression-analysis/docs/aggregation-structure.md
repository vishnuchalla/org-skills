# Aggregation Field Structure in Orion

## Critical: Use `agg:` NOT `aggregation`

The aggregation field in Orion YAML configurations is **`agg:`** (not `aggregation`), and it uses a **nested structure** with `value` and `agg_type` fields.

## Correct Structure

```yaml
metrics:
  - name: apiserverCPU
    threshold: 15
    metricName: containerCPU
    labels.namespace.keyword: openshift-kube-apiserver
    metric_of_interest: value
    agg:                      # ✅ Field name is "agg"
      value: cpu              # ✅ Field to aggregate
      agg_type: avg           # ✅ Aggregation type
    direction: 1
```

## Common Mistakes

### ❌ WRONG: Using `aggregation` field

```yaml
metrics:
  - name: apiserverCPU
    metric_of_interest: value
    aggregation: avg          # ❌ WRONG field name
```

### ❌ WRONG: Flat structure

```yaml
metrics:
  - name: apiserverCPU
    metric_of_interest: value
    agg: avg                  # ❌ WRONG structure (not nested)
```

### ❌ WRONG: Wrong nested field names

```yaml
metrics:
  - name: apiserverCPU
    metric_of_interest: value
    agg:
      field: cpu              # ❌ Should be "value"
      type: avg               # ❌ Should be "agg_type"
```

### ✅ CORRECT: Nested structure with correct field names

```yaml
metrics:
  - name: apiserverCPU
    metric_of_interest: value
    agg:
      value: cpu              # ✅ Correct
      agg_type: avg           # ✅ Correct
```

## Aggregation Types

Available `agg_type` values:

### Standard Aggregations
- **`avg`** - Average value across time series
- **`max`** - Maximum value
- **`min`** - Minimum value
- **`sum`** - Sum of values
- **`count`** - Count of data points

### Percentile Aggregations
- **`percentiles`** - Percentile analysis (used with `percentileName`)

## Examples by Metric Type

### CPU/Memory Metrics (Use avg or max)

```yaml
- name: kubeletCPU
  threshold: 12
  metricName: containerCPU
  labels.name.keyword: kubelet
  metric_of_interest: value
  agg:
    value: cpu
    agg_type: avg           # Average CPU usage
  direction: 1

- name: kubeletMemory
  threshold: 15
  metricName: containerMemory
  labels.name.keyword: kubelet
  metric_of_interest: value
  agg:
    value: memory
    agg_type: max           # Peak memory usage
  direction: 1
```

### Latency Metrics (Use avg)

```yaml
- name: etcdDiskLatency
  threshold: 15
  metricName: 99thEtcdDiskBackendCommitDurationSeconds
  metric_of_interest: value
  agg:
    value: duration
    agg_type: avg           # Average latency
  direction: 1
```

### Percentile Metrics (Use percentiles)

```yaml
- name: podReadyLatency
  threshold: 10
  metricName: podLatencyQuantilesMeasurement
  quantileName: Ready
  metric_of_interest: P99
  agg:
    value: P99
    agg_type: percentiles   # Percentile aggregation
  direction: 1
```

### Cgroup Metrics (Use avg or max)

```yaml
- name: ovsCPU
  threshold: 10
  metricName.keyword: cgroupCPU
  labels.id.keyword: /system.slice/ovs-vswitchd.service
  metric_of_interest: value
  agg:
    value: cpu
    agg_type: avg
  direction: 1
```

## When NOT to Use agg Field

### k8s-netperf Metrics

k8s-netperf data is **pre-aggregated per run**. Do NOT include `agg` field:

```yaml
# k8s-netperf pattern
metrics:
  - name: tcpStreamPodNetwork
    threshold: 10
    metric_of_interest: throughput
    profile.keyword: TCP_STREAM
    hostNetwork: "false"
    service: "false"
    # NO agg field! ✅
    direction: -1
```

### Single-Value Metrics

Some metrics return a single aggregated value per test run. These typically don't need `agg`:

```yaml
- name: schedulingThroughput
  metric_of_interest: value
  # May not need agg if data is already single-value per run
```

## Field Order (Recommended)

For readability, follow this order:

```yaml
metrics:
  - name: metricName              # 1. Name (identifier)
    threshold: 15                 # 2. Threshold (analysis parameter)
    metricName: fieldName         # 3. ES field to query
    labels.namespace.keyword: ns  # 4. Label filters
    metric_of_interest: value     # 5. Field containing the value
    agg:                          # 6. Aggregation specification
      value: cpu                  #    - What to aggregate
      agg_type: avg               #    - How to aggregate
    direction: 1                  # 7. Direction filter
    correlation: other_avg        # 8. Correlation (if any)
    labels:                       # 9. Jira labels
      - "[Jira: Component]"
```

## Validation

When Orion loads your config, it validates the structure. Common errors:

### Error: "Unknown field 'aggregation'"
```
Fix: Change `aggregation:` to `agg:`
```

### Error: "agg field must be a dict"
```yaml
# Wrong:
agg: avg

# Right:
agg:
  value: cpu
  agg_type: avg
```

### Error: "Missing required field 'agg_type'"
```yaml
# Wrong:
agg:
  value: cpu

# Right:
agg:
  value: cpu
  agg_type: avg
```

## Summary

1. **Field name**: Use `agg` (not `aggregation`)
2. **Structure**: Nested dict with `value` and `agg_type`
3. **agg_type values**: avg, max, min, sum, count, percentiles
4. **Exception**: k8s-netperf metrics do NOT use `agg` field
5. **Order**: Place after `metric_of_interest`, before `direction`

Always use the correct nested structure:

```yaml
metric_of_interest: value
agg:
  value: cpu
  agg_type: avg
```
