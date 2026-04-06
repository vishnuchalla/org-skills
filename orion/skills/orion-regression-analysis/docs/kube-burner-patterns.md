# Common Metric Patterns for OpenShift Performance Analysis

This guide provides proven metric patterns for analyzing different aspects of OpenShift cluster performance with Orion.

## Control Plane Metrics

### API Server Performance

**CPU Usage:**
```yaml
- name: apiserverCPU
  metricName: containerCPU
  labels.namespace.keyword: openshift-kube-apiserver
  metric_of_interest: value
  agg:
    value: cpu
    agg_type: avg
  threshold: 10
  direction: 1
  labels:
    - "[Jira: kube-apiserver]"
```

**Memory Usage:**
```yaml
- name: apiserverMemory
  metricName: containerMemory
  labels.namespace.keyword: openshift-kube-apiserver
  metric_of_interest: value
  agg:
    value: memory
    agg_type: max
  threshold: 15
  direction: 1
  labels:
    - "[Jira: kube-apiserver]"
```

**Request Latency:**
```yaml
- name: apiserverRequestLatency
  metricName: apiserver_request_duration_seconds
  metric_of_interest: value
  agg:
    value: duration
    agg_type: percentiles
    percents: [50, 95, 99]
    target_percentile: 99
  threshold: 20
  direction: 1
  correlation: apiserverCPU_avg
  labels:
    - "[Jira: kube-apiserver]"
```

### etcd Performance

**CPU Usage:**
```yaml
- name: etcdCPU
  metricName: containerCPU
  labels.namespace.keyword: openshift-etcd
  metric_of_interest: value
  agg:
    value: cpu
    agg_type: avg
  threshold: 10
  direction: 1
  labels:
    - "[Jira: etcd]"
```

**Disk Backend Commit Duration:**
```yaml
- name: etcdDiskBackend
  metricName: 99thEtcdDiskBackendCommitDurationSeconds
  metric_of_interest: value
  agg:
    value: duration
    agg_type: avg
  threshold: 15
  direction: 1
  correlation: etcdCPU_avg
  labels:
    - "[Jira: etcd]"
```

**WAL Fsync Duration:**
```yaml
- name: etcdWalFsync
  metricName: 99thEtcdDiskWalFsyncDurationSeconds
  metric_of_interest: value
  agg:
    value: duration
    agg_type: avg
  threshold: 15
  direction: 1
  correlation: etcdDiskBackend_avg
  labels:
    - "[Jira: etcd]"
```

**Apply Duration:**
```yaml
- name: etcdApplyDuration
  metricName: 99thEtcdNetworkPeerRoundTripTimeSeconds
  metric_of_interest: value
  agg:
    value: duration
    agg_type: avg
  threshold: 20
  direction: 1
  labels:
    - "[Jira: etcd]"
```

### OVN Kubernetes Performance

**CPU Usage:**
```yaml
- name: ovnCPU
  metricName: containerCPU
  labels.namespace.keyword: openshift-ovn-kubernetes
  metric_of_interest: value
  agg:
    value: cpu
    agg_type: avg
  threshold: 10
  direction: 1
  labels:
    - "[Jira: OVN]"
```

**Memory Usage:**
```yaml
- name: ovnMemory
  metricName: containerMemory
  labels.namespace.keyword: openshift-ovn-kubernetes
  metric_of_interest: value
  agg:
    value: memory
    agg_type: max
  threshold: 15
  direction: 1
  correlation: ovnCPU_avg
  labels:
    - "[Jira: OVN]"
```

## Node-Level Metrics

### OVS (Open vSwitch) Performance

**CPU Usage:**
```yaml
- name: ovsCPU
  metricName.keyword: cgroupCPU
  labels.id.keyword: /system.slice/ovs-vswitchd.service
  metric_of_interest: value
  agg:
    value: cpu
    agg_type: avg
  threshold: 10
  direction: 1
  labels:
    - "[Jira: Networking]"
```

**Memory Usage on Workers:**
```yaml
- name: ovsMemoryWorkers
  metricName.keyword: cgroupMemoryRSS-Workers
  labels.id.keyword: /system.slice/ovs-vswitchd.service
  metric_of_interest: value
  agg:
    value: mem
    agg_type: max
  threshold: 15
  direction: 1
  labels:
    - "[Jira: Networking]"
```

**Memory Usage on Masters:**
```yaml
- name: ovsMemoryMasters
  metricName.keyword: cgroupMemoryRSS-Masters
  labels.id.keyword: /system.slice/ovs-vswitchd.service
  metric_of_interest: value
  agg:
    value: mem
    agg_type: max
  threshold: 15
  direction: 1
  labels:
    - "[Jira: Networking]"
```

**Overall Memory Usage:**
```yaml
- name: ovsMemoryAll
  metricName.keyword: cgroupMemoryRSS
  labels.id.keyword: /system.slice/ovs-vswitchd.service
  metric_of_interest: value
  agg:
    value: mem
    agg_type: avg
  threshold: 12
  direction: 1
  correlation: ovsCPU_avg
  labels:
    - "[Jira: Networking]"
```

### Kubelet Performance

**CPU Usage:**
```yaml
- name: kubeletCPU
  metricName: containerCPU
  labels.namespace.keyword: ""
  labels.name.keyword: kubelet
  metric_of_interest: value
  agg:
    value: cpu
    agg_type: avg
  threshold: 10
  direction: 1
  labels:
    - "[Jira: Node]"
```

**Memory Usage:**
```yaml
- name: kubeletMemory
  metricName: containerMemory
  labels.namespace.keyword: ""
  labels.name.keyword: kubelet
  metric_of_interest: value
  agg:
    value: memory
    agg_type: max
  threshold: 15
  direction: 1
  correlation: kubeletCPU_avg
  labels:
    - "[Jira: Node]"
```

### Container Runtime Performance

**CRI-O CPU:**
```yaml
- name: crioCPU
  metricName.keyword: cgroupCPU
  labels.id.keyword: /system.slice/crio.service
  metric_of_interest: value
  agg:
    value: cpu
    agg_type: avg
  threshold: 10
  direction: 1
  labels:
    - "[Jira: Node]"
```

**CRI-O Memory:**
```yaml
- name: crioMemory
  metricName.keyword: cgroupMemoryRSS
  labels.id.keyword: /system.slice/crio.service
  metric_of_interest: value
  agg:
    value: mem
    agg_type: max
  threshold: 15
  direction: 1
  labels:
    - "[Jira: Node]"
```

## Application and Workload Metrics

### Pod Lifecycle Performance

**Pod Ready Latency:**
```yaml
- name: podReadyLatency
  metricName: podLatencyQuantilesMeasurement
  quantileName: Ready
  metric_of_interest: P99
  threshold: 15
  direction: 1
  not:
    jobConfig.name: garbage-collection
  labels:
    - "[Jira: PerfScale]"
```

**Pod Scheduled Latency:**
```yaml
- name: podScheduleLatency
  metricName: podLatencyQuantilesMeasurement
  quantileName: Scheduled
  metric_of_interest: P99
  threshold: 20
  direction: 1
  correlation: podReadyLatency_P99
  labels:
    - "[Jira: PerfScale]"
```

**Pod Started Latency:**
```yaml
- name: podStartLatency
  metricName: podLatencyQuantilesMeasurement
  quantileName: PodReadyToStarted
  metric_of_interest: P99
  threshold: 15
  direction: 1
  labels:
    - "[Jira: PerfScale]"
```

### Scheduling Performance

**Scheduling Throughput:**
```yaml
- name: schedulingThroughput
  metricName: schedulingThroughput
  metric_of_interest: value
  agg:
    value: throughput
    agg_type: avg
  threshold: 10
  direction: -1  # Decreases are bad
  labels:
    - "[Jira: Scheduling]"
```

**Scheduler Queue Depth:**
```yaml
- name: schedulerQueueDepth
  metricName: scheduler_queue_depth
  metric_of_interest: value
  agg:
    value: depth
    agg_type: max
  threshold: 20
  direction: 1
  labels:
    - "[Jira: Scheduling]"
```

### Network Performance

**Service Latency:**
```yaml
- name: serviceLatency
  metricName: service_request_duration
  metric_of_interest: duration_seconds
  agg:
    value: duration_seconds
    agg_type: percentiles
    percents: [50, 95, 99]
    target_percentile: 95
  threshold: 25
  direction: 1
  labels:
    - "[Jira: Networking]"
```

**Ingress Latency:**
```yaml
- name: ingressLatency
  metricName: ingress_request_duration
  metric_of_interest: duration_ms
  agg:
    value: duration_ms
    agg_type: percentiles
    percents: [50, 95, 99]
    target_percentile: 95
  threshold: 20
  direction: 1
  labels:
    - "[Jira: Ingress]"
```

## Storage Performance

### Persistent Volume Metrics

**PV Creation Time:**
```yaml
- name: pvCreationTime
  metricName: pv_creation_duration
  metric_of_interest: duration_seconds
  agg:
    value: duration_seconds
    agg_type: avg
  threshold: 30
  direction: 1
  labels:
    - "[Jira: Storage]"
```

**PVC Bind Time:**
```yaml
- name: pvcBindTime
  metricName: pvc_bind_duration
  metric_of_interest: duration_seconds
  agg:
    value: duration_seconds
    agg_type: percentiles
    percents: [50, 95, 99]
    target_percentile: 95
  threshold: 25
  direction: 1
  labels:
    - "[Jira: Storage]"
```

## Specialized Component Metrics

### Registry Performance

**Image Pull Latency:**
```yaml
- name: imagePullLatency
  metricName: image_pull_duration
  metric_of_interest: duration_seconds
  agg:
    value: duration_seconds
    agg_type: percentiles
    percents: [50, 95, 99]
    target_percentile: 95
  threshold: 30
  direction: 1
  labels:
    - "[Jira: Registry]"
```

### DNS Performance

**DNS Query Latency:**
```yaml
- name: dnsQueryLatency
  metricName: dns_query_duration
  metric_of_interest: duration_ms
  agg:
    value: duration_ms
    agg_type: percentiles
    percents: [50, 95, 99]
    target_percentile: 95
  threshold: 50
  direction: 1
  labels:
    - "[Jira: DNS]"
```

## Monitoring and Observability

### Prometheus Performance

**Prometheus CPU:**
```yaml
- name: prometheusCPU
  metricName: containerCPU
  labels.namespace.keyword: openshift-monitoring
  labels.name.keyword: prometheus
  metric_of_interest: value
  agg:
    value: cpu
    agg_type: avg
  threshold: 15
  direction: 1
  labels:
    - "[Jira: Monitoring]"
```

**Prometheus Memory:**
```yaml
- name: prometheusMemory
  metricName: containerMemory
  labels.namespace.keyword: openshift-monitoring
  labels.name.keyword: prometheus
  metric_of_interest: value
  agg:
    value: memory
    agg_type: max
  threshold: 20
  direction: 1
  correlation: prometheusCPU_avg
  labels:
    - "[Jira: Monitoring]"
```

## Metric Naming Conventions

### Naming Patterns
- **Component + Resource**: `apiserverCPU`, `etcdMemory`
- **Function + Metric**: `podReadyLatency`, `schedulingThroughput`
- **Location + Resource**: `ovsMemoryWorkers`, `kubeletCPUMasters`

### Correlation Naming
- Standard aggregations: `metricName_aggregationType`
  - Examples: `apiserverCPU_avg`, `etcdDisk_max`
- Percentiles: `metricName_percentiles`
  - Examples: `podReadyLatency_percentiles`
- Interest field: `metricName_interestField`
  - Examples: `podReadyLatency_P99`

### Labels and Organization
Use consistent labels for tracking:
```yaml
labels:
  - "[Jira: ComponentTeam]"  # For team tracking
  - "[SIG: PerformanceScale]" # For SIG tracking
  - "[Priority: High]"        # For priority tracking
```

## Best Practices

### Metric Selection
1. **Start with core infrastructure**: API server, etcd, OVN
2. **Add node-level metrics**: OVS, kubelet, container runtime
3. **Include application metrics**: Pod lifecycle, scheduling
4. **Add specialized metrics**: Based on your workload

### Threshold Setting
- **Conservative start**: 20-30% for initial analysis
- **Tune based on data**: Reduce to 10-15% for stable metrics
- **Critical components**: 5-10% for essential services
- **Noisy metrics**: 30-50% to reduce false positives

### Correlation Strategy
1. **Link related components**: etcd CPU → etcd disk latency
2. **Infrastructure dependencies**: OVN CPU → pod latency
3. **Workload correlations**: Scheduling → pod ready latency
4. **Resource correlations**: CPU → memory for same component

### Direction Configuration
- **Latency metrics**: `direction: 1` (increases are bad)
- **Throughput metrics**: `direction: -1` (decreases are bad)
- **Resource usage**: `direction: 1` (increases are bad)
- **Error rates**: `direction: 1` (increases are bad)
- **Success rates**: `direction: -1` (decreases are bad)

Remember: These patterns are starting points. Adapt field names, thresholds, and correlations based on your specific Elasticsearch schema and performance requirements.