# k8s-netperf Metric Patterns

✅ **Orion CAN analyze k8s-netperf data** with proper configuration!

**Key Requirements**:
1. **No `aggregation` field** - k8s-netperf stores pre-aggregated data
2. **Filters at metrics level** - Put `profile.keyword`, `hostNetwork`, `service` in metrics, NOT metadata
3. **Quoted boolean strings** - Use `"false"`/`"true"` (not YAML booleans `false`/`true`)
4. **Metadata for UUID matching only** - Just platform and version

**Why this structure**:
- Each test UUID contains multiple profiles (TCP_STREAM, UDP_STREAM, TCP_RR, etc.)
- Each UUID contains multiple scenarios (pod network, host network, via service, etc.)
- Filtering at metrics level lets you compare scenarios in a single test configuration

---

This guide covers performance metric patterns for k8s-netperf benchmark results. k8s-netperf tests network performance between pods in different configurations (host network, service mesh, same node, across nodes, etc.).

## k8s-netperf vs kube-burner: Key Differences

Understanding these differences explains why Orion cannot process k8s-netperf data:

| Aspect | kube-burner | k8s-netperf |
|--------|-------------|-------------|
| **Index Pattern** | `ripsaw-kube-burner-*` | `k8s-netperf-*` |
| **Timestamp Field** | `@timestamp` | `timestamp` |
| **Data Structure** | Nested (metricName → labels → value) | Flat (direct fields) |
| **Metrics** | One metric per document | Multiple metrics per test run |
| **Aggregation** | Required (avg, max, percentile) | Already aggregated per run |
| **'aggregation' field** | Present in documents | **DOES NOT EXIST** ⚠️ |
| **Orion Compatibility** | ✅ Fully supported | ✅ **Supported** (omit aggregation field) |
| **Focus** | Control plane & application metrics | Network throughput & latency |

## Test Profiles

k8s-netperf supports four standard netperf test profiles:

### TCP_STREAM (Throughput)
- **Purpose**: TCP bulk data transfer performance
- **Primary Metric**: `throughput` (Mb/s)
- **Secondary Metric**: `latency` (usec)
- **Key Field**: `tcpRetransmits` (reliability indicator)
- **Use For**: Bandwidth-intensive workload performance

### UDP_STREAM (UDP Throughput)
- **Purpose**: UDP bulk data transfer performance  
- **Primary Metric**: `throughput` (Mb/s)
- **Secondary Metric**: `latency` (usec)
- **Key Field**: `udpLossPercent` (packet loss percentage)
- **Use For**: Real-time data streaming performance

### TCP_RR (Request-Response)
- **Purpose**: TCP transaction rate performance
- **Primary Metric**: `throughput` (OP/s - operations per second)
- **Secondary Metric**: `latency` (usec - round-trip time)
- **Use For**: API call patterns, microservices communication

### TCP_CRR (Connect-Request-Response)
- **Purpose**: TCP connection establishment + transaction
- **Primary Metric**: `throughput` (OP/s)
- **Secondary Metric**: `latency` (usec - includes connection overhead)
- **Use For**: Short-lived connection patterns, HTTP requests

## Test Scenarios

k8s-netperf tests various network configurations:

### Network Mode
- **`hostNetwork: true`**: Pods use host network namespace (bypass CNI)
- **`hostNetwork: false`**: Pods use pod network (through CNI plugin)

### Communication Path
- **`service: true`**: Traffic goes through Kubernetes Service (load balancer)
- **`service: false`**: Direct pod-to-pod communication

### Locality
- **`local: true`**: Client and server on same node (intra-node)
- **`local: false`**: Client and server on different nodes (inter-node)

### Other Flags
- **`acrossAZ: true`**: Pods in different availability zones
- **`virt: true`**: Virtual machine pods (kubevirt)
- **`externalServer: true`**: Server outside the cluster

### Common Scenario Combinations

| Scenario | hostNetwork | service | local | Use Case |
|----------|-------------|---------|-------|----------|
| **Pod Network Cross-Node** | false | false | false | Most common production pattern |
| **Host Network Cross-Node** | true | false | false | Maximum performance baseline |
| **Service Cross-Node** | false | true | false | Service mesh overhead measurement |

## Key Metrics Reference

### Performance Metrics

```yaml
# Direct throughput and latency fields (already aggregated)
throughput: 982.45        # Value depends on profile
latency: 3.8              # Microseconds
tputMetric: "Mb/s"        # Or "OP/s" for RR/CRR tests
ltcyMetric: "usec"        # Always microseconds

# Reliability metrics
tcpRetransmits: 0         # TCP retransmission count
udpLossPercent: 0.6       # UDP packet loss percentage

# Confidence interval
confidence: [971.02, 993.87]  # 95% confidence bounds
```

### Test Configuration Fields

```yaml
# Test parameters
profile: "TCP_STREAM"     # TCP_STREAM, UDP_STREAM, TCP_RR, TCP_CRR
messageSize: 64           # Bytes
duration: 30              # Seconds
samples: 5                # Number of test iterations
parallelism: 2            # Concurrent connections
burst: 0                  # Burst size (0 = disabled)

# Test scenario
hostNetwork: true
service: false
local: false
acrossAZ: false
virt: false
```

### CPU Metrics

Both server and client nodes capture detailed CPU usage:

```yaml
serverCPU:
  idleCPU: 95.59          # Idle percentage
  userCPU: 0.66           # User space CPU
  systemCPU: 1.46         # Kernel space CPU
  softCPU: 1.61           # Software interrupts
  irqCPU: 0.36            # Hardware interrupts
  stealCPU: 0.003         # Stolen CPU (hypervisor)
  vSwitchCPU: 0.44        # OVS vSwitch CPU
  vSwitchMem: 48731477    # OVS memory bytes

# clientCPU has identical structure
```

### Pod-Level Metrics

Per-pod CPU and memory during the test:

```yaml
serverPods:
  - podName: "server-55bcfdfdcd-75s9v"
    cpuUsage: 4.91        # CPU cores (millicores/1000)
  - podName: "ovnkube-node-pcr4s"
    cpuUsage: 1.27

serverPodsMem:
  - podName: "ovnkube-node-pcr4s"
    memUsage: 282912085   # Bytes

# clientPods and clientPodsMem have identical structure
```

### Metadata Structure

Similar to kube-burner but nested under `metadata`:

```yaml
metadata:
  platform: "AWS"
  clusterType: "self-managed"
  ocpVersion: "5.0.0-0.nightly-2026-02-22-002254"
  ocpMajorVersion: "5.0"
  k8sVersion: "v1.34.2"
  sdnType: "OVNKubernetes"
  region: "us-west-2"
  workerNodesCount: 9
  totalNodes: 15
  kernel: "5.14.0-570.93.1.el9_6.x86_64"
  mtu: 9001
  ipsecMode: "Disabled"
```

## Orion Configuration Patterns

### **Critical Configuration Requirements**

✅ **Correct pattern** for k8s-netperf:
```yaml
tests:
  - name: network-performance
    metadata:
      # Metadata: ONLY platform/version (for UUID matching)
      metadata.platform: AWS
      metadata.ocpMajorVersion: "5.0"
    metrics:
      - name: tcpStreamPodNetwork
        metric_of_interest: throughput
        # All filters at METRICS level:
        profile.keyword: TCP_STREAM
        hostNetwork: "false"  # Quoted string, not YAML boolean!
        service: "false"
        # NO aggregation field!
        threshold: 10
        direction: -1
```

❌ **Common mistakes**:
1. ❌ Adding `aggregation` field → causes empty DataFrames
2. ❌ Putting `profile.keyword` at metadata level → can't analyze multiple profiles in one test
3. ❌ Using YAML booleans `false` → becomes 'False' (capitalized), doesn't match ES
4. ❌ Putting `hostNetwork`/`service` at metadata level → prevents scenario comparison

### Basic TCP_STREAM Throughput Monitoring

Monitor TCP throughput regressions with scenario filtering:

```yaml
tests:
  - name: tcp-stream-analysis
    metadata:
      metadata.platform: AWS
      metadata.ocpMajorVersion: "{{ version }}"
    metrics:
      # Pod Network (through CNI)
      - name: tcpStreamPodNetwork
        metric_of_interest: throughput
        profile.keyword: TCP_STREAM
        hostNetwork: "false"  # Quoted string!
        service: "false"
        threshold: 10
        direction: -1
        
      # Host Network (baseline)
      - name: tcpStreamHostNetwork
        metric_of_interest: throughput
        profile.keyword: TCP_STREAM
        hostNetwork: "true"
        service: "false"
        threshold: 10
        direction: -1
```

### Multi-Profile Network Analysis

Compare different test profiles in one config:

```yaml
tests:
  - name: tcp-stream-throughput
    metadata:
      benchmark.keyword: k8s-netperf
      metadata.platform: "{{ platform }}"
      profile.keyword: TCP_STREAM
      hostNetwork: false
      service: false
    metrics:
      - name: bandwidth
        metric_of_interest: throughput
        # NO agg field - k8s-netperf data is pre-aggregated!
        threshold: 10
        direction: -1

  - name: tcp-rr-latency
    metadata:
      benchmark.keyword: k8s-netperf
      metadata.platform: "{{ platform }}"
      profile.keyword: TCP_RR
      hostNetwork: false
      service: false
    metrics:
      - name: transactionRate
        metric_of_interest: throughput
        # NO agg field - k8s-netperf data is pre-aggregated!
        threshold: 15
        direction: -1
        
      - name: rtt
        metric_of_interest: latency
        # NO agg field - k8s-netperf data is pre-aggregated!
        threshold: 20
        direction: 1

  - name: udp-stream-reliability
    metadata:
      benchmark.keyword: k8s-netperf
      metadata.platform: "{{ platform }}"
      profile.keyword: UDP_STREAM
      hostNetwork: false
      service: false
    metrics:
      - name: udpBandwidth
        metric_of_interest: throughput
        # NO agg field - k8s-netperf data is pre-aggregated!
        threshold: 10
        direction: -1
        
      - name: packetLoss
        metric_of_interest: udpLossPercent
        # NO agg field - k8s-netperf data is pre-aggregated!
        threshold: 25
        direction: 1  # Higher loss is bad
```

### Scenario Comparison

Compare pod network vs host network performance:

```yaml
tests:
  - name: pod-network-tcp-stream
    metadata:
      benchmark.keyword: k8s-netperf
      profile.keyword: TCP_STREAM
      hostNetwork: false
      service: false
      metadata.sdnType: OVNKubernetes
    metrics:
      - name: podNetThroughput
        metric_of_interest: throughput
        # NO agg field - k8s-netperf data is pre-aggregated!
        threshold: 10
        direction: -1

  - name: host-network-tcp-stream
    metadata:
      benchmark.keyword: k8s-netperf
      profile.keyword: TCP_STREAM
      hostNetwork: true
      service: false
    metrics:
      - name: hostNetThroughput
        metric_of_interest: throughput
        # NO agg field - k8s-netperf data is pre-aggregated!
        threshold: 10
        direction: -1
```

### Service Mesh Overhead

Monitor service vs direct pod-to-pod performance:

```yaml
tests:
  - name: service-overhead-analysis
    metadata:
      benchmark.keyword: k8s-netperf
      profile.keyword: TCP_RR
      hostNetwork: false
      service: true
      metadata.platform: AWS
    metrics:
      - name: serviceTransactionRate
        metric_of_interest: throughput
        # NO agg field - k8s-netperf data is pre-aggregated!
        threshold: 15
        direction: -1
        
      - name: serviceLatency
        metric_of_interest: latency
        # NO agg field - k8s-netperf data is pre-aggregated!
        threshold: 20
        direction: 1
```

### Infrastructure Impact Monitoring

Track OVS and node CPU impact during network tests:

```yaml
tests:
  - name: network-infrastructure-load
    metadata:
      benchmark.keyword: k8s-netperf
      profile.keyword: TCP_STREAM
      metadata.platform: AWS
      metadata.ocpMajorVersion: "{{ version }}"
    metrics:
      - name: serverVswitchCpu
        metric_of_interest: serverVswtichCpu  # Note: typo in actual field
        # NO agg field - k8s-netperf data is pre-aggregated!
        threshold: 25
        direction: 1
        
      - name: clientVswitchCpu
        metric_of_interest: clientVswtichCpu
        # NO agg field - k8s-netperf data is pre-aggregated!
        threshold: 25
        direction: 1
        
      - name: serverSystemCpu
        metric_of_interest: serverCPU.systemCPU
        # NO agg field - k8s-netperf data is pre-aggregated!
        threshold: 20
        direction: 1
```

## Discovery Queries for k8s-netperf

### Find Available Test Profiles

```bash
curl -s -u "$USER:$PASS" "$ES_SERVER/k8s-netperf-*/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "aggs": {
      "profiles": {
        "terms": {"field": "profile.keyword", "size": 50}
      }
    }
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
for b in data['aggregations']['profiles']['buckets']:
    print(f'{b[\"key\"]:30} {b[\"doc_count\"]:>6} runs')
"
```

### Find Test Scenarios

```bash
curl -s -u "$USER:$PASS" "$ES_SERVER/k8s-netperf-*/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "aggs": {
      "scenarios": {
        "multi_terms": {
          "terms": [
            {"field": "hostNetwork"},
            {"field": "service"},
            {"field": "local"}
          ],
          "size": 20
        }
      }
    }
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('Test scenarios (hostNetwork, service, local):')
for s in data['aggregations']['scenarios']['buckets']:
    keys = s['key']
    print(f'hostNet={keys[0]}, service={keys[1]}, local={keys[2]}: {s[\"doc_count\"]} runs')
"
```

### Get Throughput Statistics by Profile

```bash
curl -s -u "$USER:$PASS" "$ES_SERVER/k8s-netperf-*/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "query": {
      "term": {"profile.keyword": "TCP_STREAM"}
    },
    "aggs": {
      "throughput_stats": {
        "stats": {"field": "throughput"}
      }
    }
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
stats = data['aggregations']['throughput_stats']
print(f'TCP_STREAM Throughput Statistics:')
print(f'  Count: {stats[\"count\"]}')
print(f'  Average: {stats[\"avg\"]:.2f} Mb/s')
print(f'  Min: {stats[\"min\"]:.2f} Mb/s')
print(f'  Max: {stats[\"max\"]:.2f} Mb/s')
"
```

### Find SDN Types Tested

```bash
curl -s -u "$USER:$PASS" "$ES_SERVER/k8s-netperf-*/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "aggs": {
      "sdnTypes": {
        "terms": {"field": "metadata.sdnType.keyword", "size": 20}
      }
    }
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
for b in data['aggregations']['sdnTypes']['buckets']:
    print(f'{b[\"key\"]:30} {b[\"doc_count\"]:>6} tests')
"
```

### Sample Full Document

```bash
curl -s -u "$USER:$PASS" "$ES_SERVER/k8s-netperf-*/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 1,
    "query": {
      "bool": {
        "must": [
          {"term": {"profile.keyword": "TCP_RR"}},
          {"term": {"hostNetwork": false}},
          {"term": {"service": false}}
        ]
      }
    }
  }' | python3 -m json.tool
```

## Common Analysis Patterns

### Throughput Regression Detection

**Goal**: Detect when network throughput drops across OCP versions

**Strategy**:
- Use `--hunter-analyze` for statistical changepoint detection
- Monitor both `throughput` and `latency`
- Separate tests by profile (TCP_STREAM, UDP_STREAM, TCP_RR)
- Include `tcpRetransmits` and `udpLossPercent` for context

**Thresholds**:
- Throughput (TCP_STREAM, UDP_STREAM): 10-15% drop
- Transaction rate (TCP_RR, TCP_CRR): 15-20% drop
- Latency: 20% increase
- Retransmits/Loss: Any increase >25%

### Service Mesh Overhead

**Goal**: Measure performance impact of service routing

**Strategy**:
- Compare `service: true` vs `service: false`
- Use correlation between tests
- Monitor both throughput and latency impact

### CNI Plugin Performance

**Goal**: Compare network plugin performance

**Strategy**:
- Group by `metadata.sdnType`
- Use `hostNetwork: true` as baseline
- Measure pod network overhead

### Multi-AZ Latency

**Goal**: Monitor cross-AZ network performance

**Strategy**:
- Filter by `acrossAZ: true`
- Focus on latency more than throughput
- Compare same-AZ vs cross-AZ

## Tips for k8s-netperf Analysis

### Configuration Best Practices

1. **Always specify profile**: Don't mix TCP_STREAM and TCP_RR in same test (different units!)
2. **Match scenario flags**: Be specific with hostNetwork, service, local combinations
3. **Use appropriate thresholds**: Throughput tests are more stable (10%) than latency tests (20%)
4. **Monitor infrastructure**: Include vSwitch CPU/memory for CNI overhead analysis
5. **Check reliability metrics**: tcpRetransmits and udpLossPercent can explain throughput drops

### Common Pitfalls

1. **Mixed metrics**: Don't compare Mb/s (STREAM) with OP/s (RR) in same analysis
2. **Scenario confusion**: `hostNetwork: true` tests bypass CNI - don't compare with pod network
3. **Missing context**: Always check `messageSize` - different sizes have different performance profiles
4. **Field names**: Note `vSwitchCPU` has inconsistent spelling (`serverVswtichCpu` - typo in actual data)

### Orion-Specific Considerations

Since k8s-netperf data is already aggregated:
- **Do NOT use `agg` or `aggregation` fields** - k8s-netperf data is pre-aggregated per run
- Orion automatically averages across multiple runs without needing aggregation specification
- The `confidence` array shows test variance - check when results are inconsistent
- `samples` field tells you how many iterations were averaged

## Example Command

Running Orion analysis on k8s-netperf data:

```bash
orion --config k8s-netperf.yaml --hunter-analyze \
  --es-server='https://user:pass@es-server.com' \
  --benchmark-index='k8s-netperf-*' \
  --metadata-index='k8s-netperf-*' \
  --lookback=30d \
  --viz
```

**Note**: For k8s-netperf, both benchmark and metadata indices are the same (`k8s-netperf-*`), unlike kube-burner which uses separate indices.

## Related Documentation

- **[ES Discovery Guide](es-discovery-guide.md)**: Query patterns to explore k8s-netperf data
- **[Config Building Guide](config-building-guide.md)**: General Orion configuration principles
- **[kube-burner Patterns](kube-burner-patterns.md)**: kube-burner metric patterns (complementary)
- **[Troubleshooting](troubleshooting.md)**: Common issues and solutions
