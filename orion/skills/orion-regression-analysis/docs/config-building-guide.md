# How to Build Orion Configurations

This guide teaches you how to create effective Orion configuration files for detecting performance regressions in OpenShift environments.

## Configuration Structure

Every Orion configuration follows this basic structure:

```yaml
tests:
  - name: descriptive-test-name
    metadata:
      # Elasticsearch query filters to find your test data
    metrics:
      # Performance metrics to analyze for regressions
```

## Building Metadata Filters

Metadata acts as Elasticsearch query filters to locate your specific test data. Think of it as a search query that finds the exact test runs you want to analyze.

### Platform & Infrastructure Filters

**Cloud Platform:**
```yaml
metadata:
  platform: AWS          # AWS|GCP|Azure|BareMetal
  clusterType: self-managed  # self-managed|managed (for ROSA/ARO)
```

**Cluster Configuration:**
```yaml
metadata:
  masterNodesCount: 3
  workerNodesCount: 6
  masterNodesType: m6a.xlarge
  workerNodesType: m6a.xlarge
```

**Network Configuration:**
```yaml
metadata:
  networkType: OVNKubernetes  # OVNKubernetes|OpenShiftSDN
  encrypted: true              # For encryption testing
  fips: false                  # FIPS compliance testing
  ipsec: false                 # IPsec testing
```

### Test Identification Filters

**Benchmark Types:**
```yaml
metadata:
  benchmark.keyword: cluster-density-v2  # cluster-density-v2|node-density|ingress|netperf
```

**OpenShift Version:**
```yaml
metadata:
  ocpVersion: "4.22"          # Static version
  ocpVersion: "{{ version }}" # Template variable
```

**Job Identification:**
```yaml
metadata:
  jobType: periodic           # periodic|presubmit|postsubmit
  pullNumber: "{{ pull_number }}"  # For PR analysis
```

### Dynamic Variables with Templating

Use Jinja2 templating to make configs reusable:

```yaml
metadata:
  ocpVersion: "{{ version }}"
  benchmark.keyword: "{{ benchmark | default('cluster-density-v2') }}"
  workerNodesCount: "{{ numWorkers | default('6') }}"
  platform: "{{ platform | default('AWS') }}"
```

Run with variables:
```bash
orion --config config.yaml --input-vars='{"version": "4.22", "benchmark": "node-density"}'
```

### Exclusion Filters

Exclude specific data using the `not` keyword:

```yaml
metadata:
  not:
    stream: okd                    # Exclude OKD runs
    jobConfig.name: garbage-collection  # Exclude specific job configs
```

Exclude multiple values:
```yaml
metadata:
  not:
    service_mesh_mode:
      - ambient
      - sidecar
```

## Designing Metrics

Each metric defines what performance data to analyze for regressions.

### Basic Metric Structure

```yaml
metrics:
  - name: descriptive-name           # Used in reports and correlation
    metricName: elasticsearch-field  # Field name in your ES index
    metric_of_interest: field-to-analyze  # Which subfield to analyze
```

### Metric Types and Patterns

**Latency Metrics (Lower is Better):**
```yaml
- name: podReadyLatency
  metricName: podLatencyQuantilesMeasurement
  quantileName: Ready
  metric_of_interest: P99        # P50, P95, P99 for percentiles
  direction: 1                   # Only detect increases (regressions)
  threshold: 15                  # 15% increase threshold
```

**Resource Usage Metrics:**
```yaml
- name: apiserverCPU
  metricName: containerCPU
  labels.namespace.keyword: openshift-kube-apiserver
  metric_of_interest: value
  agg:
    value: cpu
    agg_type: avg               # avg|max|sum|count
  direction: 1                  # Only detect increases
  threshold: 10                 # 10% increase threshold
```

**Count Metrics (Volume):**
```yaml
- name: apiRequestCount
  metricName: api_requests
  metric_of_interest: request_id
  agg:
    value: request_id
    agg_type: count
  direction: -1                 # Only detect decreases (bad)
```

### Aggregation Types

**Standard Aggregations:**
- `avg`: Average across all values
- `max`: Maximum value found
- `min`: Minimum value found
- `sum`: Sum of all values
- `count`: Number of data points

**Percentile Aggregations:**
```yaml
- name: latencyP99
  metricName: response_time
  metric_of_interest: duration_ms
  agg:
    value: duration_ms
    agg_type: percentiles
    percents: [50, 95, 99, 99.9]    # Which percentiles to calculate
    target_percentile: 99           # Which to analyze for regressions
```

### Field Selection

**Namespace Filtering:**
```yaml
labels.namespace.keyword: openshift-kube-apiserver
```

**Label-based Filtering:**
```yaml
labels.id.keyword: /system.slice/ovs-vswitchd.service
```

**Quantile Selection:**
```yaml
quantileName: Ready              # For pod latency metrics
```

## Setting Detection Parameters

### Direction Control

Choose which types of changes to detect:

```yaml
direction: 1    # Only increases (regressions for latency/CPU)
direction: -1   # Only decreases (regressions for throughput)
direction: 0    # Both increases and decreases (default)
```

### Threshold Configuration

Set minimum percentage change to detect:

```yaml
# Test-level (applies to all metrics)
tests:
  - name: my-test
    threshold: 15    # 15% change minimum
    metrics:
      # metrics inherit 15% threshold

# Metric-level (overrides test level)
- name: criticalMetric
  threshold: 5     # 5% change minimum for this metric
```

### Correlation Analysis

Link metrics so detection only happens when related metrics also change:

```yaml
- name: podLatency
  correlation: apiserverCPU_avg    # Only detect if API server CPU also changed
  
- name: etcdLatency  
  correlation: etcdCPU_avg         # Link to etcd CPU usage
```

**Correlation Name Format:** `metric_name_aggregation_type`
- Examples: `apiserverCPU_avg`, `ovnCPU_avg`, `podLatency_P99`

### Context Analysis

Analyze runs before and after changepoints:

```yaml
- name: podLatency
  correlation: apiserverCPU_avg
  context: 5                      # Analyze 5 runs before/after
```

## Configuration Inheritance

Reduce duplication using inheritance patterns:

### Parent Configuration

**shared-metadata.yaml:**
```yaml
metadata:
  platform: AWS
  clusterType: self-managed
  masterNodesCount: 3
  workerNodesCount: 6
  networkType: OVNKubernetes
```

### Child Configuration

**test-config.yaml:**
```yaml
parentConfig: shared-metadata.yaml
tests:
  - name: cluster-density-test
    metadata:
      benchmark.keyword: cluster-density-v2
      ocpVersion: "{{ version }}"
      # Inherits all parent metadata
    metrics:
      # Define test-specific metrics
```

### Shared Metrics

**common-metrics.yaml:**
```yaml
- name: podReadyLatency
  metricName: podLatencyQuantilesMeasurement
  quantileName: Ready
  metric_of_interest: P99
  threshold: 15
  direction: 1

- name: apiserverCPU
  metricName: containerCPU
  labels.namespace.keyword: openshift-kube-apiserver
  metric_of_interest: value
  agg:
    value: cpu
    agg_type: avg
  threshold: 10
  direction: 1
```

**test-config.yaml:**
```yaml
metricsFile: common-metrics.yaml
tests:
  - name: my-test
    metadata:
      # metadata filters
    metrics:
      # Additional test-specific metrics
      # Inherits all metrics from common-metrics.yaml
```

### Local Overrides

Override inheritance for specific tests:

```yaml
tests:
  - name: special-test
    local_config: special-metadata.yaml    # Use different metadata
    local_metrics: special-metrics.yaml    # Use different metrics
    metadata:
      # Additional metadata on top of local_config
    metrics:
      # Additional metrics on top of local_metrics

  - name: isolated-test
    IgnoreGlobal: true          # Don't inherit global parentConfig
    IgnoreGlobalMetrics: true   # Don't inherit global metricsFile
    metadata:
      # Only use this metadata
    metrics:
      # Only use these metrics
```

## Common Configuration Patterns

### Control Plane Performance Test
```yaml
tests:
  - name: control-plane-performance
    metadata:
      platform: AWS
      benchmark.keyword: cluster-density-v2
      ocpVersion: "{{ version }}"
    metrics:
      - name: apiserverCPU
        metricName: containerCPU
        labels.namespace.keyword: openshift-kube-apiserver
        metric_of_interest: value
        agg: {value: cpu, agg_type: avg}
        threshold: 10
        direction: 1
        
      - name: etcdDisk
        metricName: 99thEtcdDiskBackendCommitDurationSeconds
        metric_of_interest: value
        correlation: etcdCPU_avg
        threshold: 15
        direction: 1
```

### Node Performance Test
```yaml
tests:
  - name: node-performance
    metadata:
      platform: AWS
      benchmark.keyword: node-density
      ocpVersion: "{{ version }}"
    metrics:
      - name: ovsCPU
        metricName.keyword: cgroupCPU
        labels.id.keyword: /system.slice/ovs-vswitchd.service
        metric_of_interest: value
        agg: {value: cpu, agg_type: avg}
        threshold: 10
        direction: 1
        
      - name: kubeletMemory
        metricName: containerMemory
        labels.namespace.keyword: ""
        labels.name.keyword: kubelet
        metric_of_interest: value
        agg: {value: memory, agg_type: max}
        threshold: 15
        direction: 1
```

### Application Performance Test
```yaml
tests:
  - name: application-performance
    threshold: 15    # Default for all metrics
    metadata:
      platform: AWS
      benchmark.keyword: cluster-density-v2
      ocpVersion: "{{ version }}"
    metrics:
      - name: podReadyLatency
        metricName: podLatencyQuantilesMeasurement
        quantileName: Ready
        metric_of_interest: P99
        direction: 1
        
      - name: scheduleLatency
        metricName: podLatencyQuantilesMeasurement  
        quantileName: Scheduled
        metric_of_interest: P99
        correlation: podReadyLatency_P99
        direction: 1
```

## Validation and Testing

### Configuration Validation
- Use `--debug` flag to see generated Elasticsearch queries
- Verify metadata filters match your data structure
- Test with small lookback periods first (`--lookback=1d`)
- Check metric names match your Elasticsearch index fields

### Iterative Development
1. Start with basic metadata filters
2. Add one metric at a time
3. Tune thresholds based on initial results
4. Add correlation after understanding individual metrics
5. Optimize with inheritance once patterns emerge

### Common Mistakes
- **Too broad metadata**: Matches unrelated test data
- **Too narrow metadata**: No data found
- **Wrong metric names**: Check Elasticsearch field names
- **Missing aggregations**: Required for multi-value metrics
- **Incorrect direction**: Shows wrong type of regressions
- **Thresholds too low**: Too many false positives
- **Thresholds too high**: Missing real regressions

Remember: Good configurations balance sensitivity (catching real regressions) with specificity (avoiding false positives). Start conservative and tune based on results.