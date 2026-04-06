# Elasticsearch Discovery Guide

This guide helps you explore your Elasticsearch data to discover available metrics, fields, and values for creating Orion configurations.

## Using the Discovery Script (Recommended)

The easiest way to discover your ES data is using the `discover-es-data.py` script:

```bash
# Discover available benchmarks
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml benchmarks

# Discover metrics for a benchmark
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml metrics --benchmark cluster-density-v2

# Discover namespaces for a metric
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml namespaces --metric containerCPU

# Discover platforms
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml platforms

# Discover OCP versions
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml versions --benchmark cluster-density-v2

# Get sample document structure
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml sample --benchmark cluster-density-v2

# For k8s-netperf:
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml --index k8s-netperf-* profiles
python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml --index k8s-netperf-* scenarios --profile TCP_STREAM
```

## Manual Discovery Commands (Advanced)

All commands assume you have ES credentials configured. Replace:
- `user:pass` with your credentials
- `es-server.com` with your ES server URL
- `benchmark-name` with your specific benchmark

### 1. Find Available Benchmarks

See what test types are in your ES data:

```bash
curl -s -u "user:pass" "https://es-server.com/perf_scale_ci*/_search" \
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
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
benchmarks = data['aggregations']['benchmarks']['buckets']
print('\nAvailable Benchmarks:')
print('='*70)
for b in benchmarks:
    print(f'{b[\"key\"]:45} {b[\"doc_count\"]:>8} runs')
"
```

### 2. Discover Metrics for a Benchmark

Find all available metrics for a specific test:

```bash
curl -s -u "user:pass" "https://es-server.com/ripsaw-kube-burner-*/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "query": {
      "term": {"benchmark.keyword": "cluster-density-v2"}
    },
    "aggs": {
      "metrics": {
        "terms": {
          "field": "metricName.keyword",
          "size": 200
        }
      }
    }
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
metrics = data['aggregations']['metrics']['buckets']
print('\nAvailable Metrics:')
print('='*70)
for m in metrics:
    print(f'{m[\"key\"]:60} {m[\"doc_count\"]:>8}')
"
```

### 3. Find Namespaces for Container Metrics

Discover which namespaces have containerCPU/Memory data:

```bash
curl -s -u "user:pass" "https://es-server.com/ripsaw-kube-burner-*/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "query": {
      "bool": {
        "must": [
          {"term": {"benchmark.keyword": "cluster-density-v2"}},
          {"term": {"metricName.keyword": "containerCPU"}}
        ]
      }
    },
    "aggs": {
      "namespaces": {
        "terms": {
          "field": "labels.namespace.keyword",
          "size": 100
        }
      }
    }
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
namespaces = data['aggregations']['namespaces']['buckets']
print('\nNamespaces with containerCPU data:')
print('='*70)
for ns in namespaces:
    if ns['key']:  # Skip empty namespaces
        print(f'{ns[\"key\"]:55} {ns[\"doc_count\"]:>8} samples')
"
```

### 4. Find Cgroup Services

Discover available cgroup paths for node metrics:

```bash
curl -s -u "user:pass" "https://es-server.com/ripsaw-kube-burner-*/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "query": {
      "bool": {
        "must": [
          {"term": {"benchmark.keyword": "node-density"}},
          {"term": {"metricName.keyword": "cgroupCPU"}}
        ]
      }
    },
    "aggs": {
      "services": {
        "terms": {
          "field": "labels.id.keyword",
          "size": 100
        }
      }
    }
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
services = data['aggregations']['services']['buckets']
print('\nAvailable Cgroup Services:')
print('='*70)
for svc in services:
    print(f'{svc[\"key\"]:60} {svc[\"doc_count\"]:>8}')
"
```

### 5. Find Quantile Names

For latency metrics, discover available quantiles:

```bash
curl -s -u "user:pass" "https://es-server.com/ripsaw-kube-burner-*/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "query": {
      "term": {"metricName.keyword": "podLatencyQuantilesMeasurement"}
    },
    "aggs": {
      "quantiles": {
        "terms": {
          "field": "quantileName.keyword",
          "size": 50
        }
      }
    }
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
quantiles = data['aggregations']['quantiles']['buckets']
print('\nAvailable Quantile Names:')
print('='*70)
for q in quantiles:
    print(f'{q[\"key\"]:30} {q[\"doc_count\"]:>8} measurements')
"
```

### 6. Sample Document Structure

See the actual structure of a metric:

```bash
curl -s -u "user:pass" "https://es-server.com/ripsaw-kube-burner-*/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 1,
    "query": {
      "bool": {
        "must": [
          {"term": {"benchmark.keyword": "cluster-density-v2"}},
          {"term": {"metricName.keyword": "containerCPU"}}
        ]
      }
    }
  }' | python3 -m json.tool | head -50
```

### 7. Find Available Platforms

See what platforms have data:

```bash
curl -s -u "user:pass" "https://es-server.com/perf_scale_ci*/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "aggs": {
      "platforms": {
        "terms": {
          "field": "platform.keyword",
          "size": 20
        }
      }
    }
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
platforms = data['aggregations']['platforms']['buckets']
print('\nAvailable Platforms:')
print('='*70)
for p in platforms:
    print(f'{p[\"key\"]:30} {p[\"doc_count\"]:>8} runs')
"
```

### 8. Find OCP Versions

Discover what versions have test data:

```bash
curl -s -u "user:pass" "https://es-server.com/perf_scale_ci*/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "query": {
      "term": {"benchmark.keyword": "cluster-density-v2"}
    },
    "aggs": {
      "versions": {
        "terms": {
          "field": "ocpVersion.keyword",
          "size": 50
        }
      }
    }
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
versions = data['aggregations']['versions']['buckets']
print('\nOCP Versions with data:')
print('='*70)
for v in sorted(versions, key=lambda x: x['key'], reverse=True)[:20]:
    print(f'{v[\"key\"]:50} {v[\"doc_count\"]:>6} runs')
"
```

## Discovery Workflow for Creating Configs

### Step-by-Step Example: Creating Network Performance Config

**1. Find your benchmark**
```bash
# Run benchmark discovery (command #1)
# Find: udn-density-pods
```

**2. Discover network-related metrics**
```bash
# Run metric discovery for udn-density-pods
curl -s -u "user:pass" "https://es-server.com/ripsaw-kube-burner-*/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "query": {"term": {"benchmark.keyword": "udn-density-pods"}},
    "aggs": {"metrics": {"terms": {"field": "metricName.keyword", "size": 100}}}
  }' | python3 -c "import sys, json; data = json.load(sys.stdin); [print(b['key']) for b in data['aggregations']['metrics']['buckets']]"
```

**3. For containerCPU, find OVN namespace**
```bash
# Run namespace discovery (command #3)
# Find: openshift-ovn-kubernetes
```

**4. For cgroupCPU, find OVS service**
```bash
# Run cgroup discovery (command #4)
# Find: /system.slice/ovs-vswitchd.service
```

**5. Check pod latency quantiles**
```bash
# Run quantile discovery (command #5)
# Find: Ready, Scheduled, Started
```

**6. Create config with discovered values**

Now you have all the information to create an accurate config!

## Common Discovery Scenarios

### "I want to monitor etcd performance"

```bash
# 1. Find etcd-specific metrics
curl -s -u "user:pass" "https://es-server.com/ripsaw-kube-burner-*/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "query": {"wildcard": {"metricName.keyword": "*etcd*"}},
    "aggs": {"metrics": {"terms": {"field": "metricName.keyword", "size": 50}}}
  }' | python3 -c "import sys, json; data = json.load(sys.stdin); [print(b['key']) for b in data['aggregations']['metrics']['buckets']]"

# Results might include:
# - 99thEtcdDiskBackendCommitDurationSeconds
# - etcdLeaderChanges
# - containerCPU (with namespace: openshift-etcd)
```

### "What node-level metrics are available?"

```bash
# Find all cgroup metrics
curl -s -u "user:pass" "https://es-server.com/ripsaw-kube-burner-*/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "query": {"prefix": {"metricName.keyword": "cgroup"}},
    "aggs": {"metrics": {"terms": {"field": "metricName.keyword", "size": 50}}}
  }' | python3 -c "import sys, json; data = json.load(sys.stdin); [print(b['key']) for b in data['aggregations']['metrics']['buckets']]"
```

## Tips

1. **Start broad, then narrow**: Find benchmarks → metrics → specific fields
2. **Use filters**: Always filter by benchmark for relevant results
3. **Check counts**: High doc counts = reliable data
4. **Sample data**: When unsure about structure, get a sample document
5. **Keywords**: Use `.keyword` fields for aggregations
6. **Wildcards**: Use for exploratory searches (`*cpu*`, `*memory*`)

## Integration with Claude

Claude can use the discovery script for you! Just ask:
- "What benchmarks are available in my ES data?"
- "What metrics are available for cluster-density-v2?"
- "Show me k8s-netperf test profiles"
- "What platforms have data?"
- "Find network-related metrics"

Claude will run `discover-es-data.py` with appropriate options and help you build configs with the results.
