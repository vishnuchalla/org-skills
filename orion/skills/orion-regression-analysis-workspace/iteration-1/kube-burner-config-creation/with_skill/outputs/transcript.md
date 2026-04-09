# Orion Config Creation Transcript

## User Request

> I need to create an Orion config to monitor control plane performance for cluster-density-v2 on AWS with OCP 4.18. I want to track API server CPU, etcd disk commit latency, and OVN kubernetes memory. We have 3 m6a.xlarge masters and 6 m6a.xlarge workers. My ES config is already set up at ~/.orion/elasticsearch-config.yaml.

## Response

Since your Elasticsearch configuration is already set up at `~/.orion/elasticsearch-config.yaml`, we can proceed directly to creating your Orion analysis config.

Based on your requirements, I've created a configuration file that monitors three key control plane metrics for `cluster-density-v2` on AWS with OCP 4.18. Here is what the config covers and why each metric matters:

### Configuration Summary

**File:** `cluster-density-v2-controlplane-aws.yaml`

**Metadata Filters:**
- **Platform:** AWS
- **Cluster Type:** self-managed
- **Network Type:** OVNKubernetes
- **Benchmark:** cluster-density-v2
- **OCP Version:** 4.18
- **Node Configuration:** 3 m6a.xlarge masters, 6 m6a.xlarge workers
- **Exclusions:** OKD stream runs and garbage-collection job configs are excluded to avoid polluting results with non-standard test runs.

### Metrics Tracked

#### 1. API Server CPU (`apiserverCPU`)
- **What it monitors:** Average CPU consumption of the `openshift-kube-apiserver` containers.
- **Why it matters:** The API server is the central hub for all cluster operations. CPU increases indicate the control plane is under heavier load, which can degrade responsiveness for kubectl commands, controller reconciliation, and workload scheduling.
- **Metric field:** `containerCPU` filtered to `openshift-kube-apiserver` namespace.
- **Aggregation:** `avg` of CPU values across all API server pods.
- **Threshold:** 10% -- relatively sensitive because this is a critical component.
- **Direction:** 1 (only increases are flagged as regressions).

#### 2. etcd Disk Backend Commit Latency (`etcdDiskBackendCommitLatency`)
- **What it monitors:** The 99th percentile of etcd's disk backend commit duration.
- **Why it matters:** etcd is the cluster's key-value store. High disk commit latency indicates storage I/O pressure, which can cause slow API responses, leader election instability, and in severe cases, cluster outages.
- **Metric field:** `99thEtcdDiskBackendCommitDurationSeconds`.
- **Aggregation:** `avg` of duration values.
- **Threshold:** 15% -- slightly more tolerant since disk latency can have natural variance.
- **Direction:** 1 (only increases are regressions).
- **Correlation:** Linked to `apiserverCPU_avg` -- when etcd latency increases alongside API server CPU, it helps confirm the regression is real and may indicate a broader control plane issue rather than isolated noise.

#### 3. OVN Kubernetes Memory (`ovnKubernetesMemory`)
- **What it monitors:** Peak memory consumption of OVN Kubernetes networking components in the `openshift-ovn-kubernetes` namespace.
- **Why it matters:** Memory growth in the network layer can indicate memory leaks or scaling issues. Unchecked growth leads to OOM kills, which cause network disruptions and pod connectivity failures.
- **Metric field:** `containerMemory` filtered to `openshift-ovn-kubernetes` namespace.
- **Aggregation:** `max` of memory values (peak is more relevant than average for detecting leaks).
- **Threshold:** 15%.
- **Direction:** 1 (only increases are regressions).
- **Correlation:** Linked to `apiserverCPU_avg` to catch correlated control plane regressions.

### How to Run the Analysis

Since your ES config is at `~/.orion/elasticsearch-config.yaml`, you can run the analysis with:

```bash
orion --config cluster-density-v2-controlplane-aws.yaml --hunter-analyze \
  --es-server='<your-es-server-url-from-config>' \
  --benchmark-index='ripsaw-kube-burner-*' \
  --metadata-index='perf_scale_ci*' \
  --lookback=15d
```

For a visual report with charts:

```bash
orion --config cluster-density-v2-controlplane-aws.yaml --hunter-analyze \
  --es-server='<your-es-server-url-from-config>' \
  --benchmark-index='ripsaw-kube-burner-*' \
  --metadata-index='perf_scale_ci*' \
  --lookback=15d --viz
```

To save results for later review:

```bash
orion --config cluster-density-v2-controlplane-aws.yaml --hunter-analyze \
  --es-server='<your-es-server-url-from-config>' \
  --benchmark-index='ripsaw-kube-burner-*' \
  --metadata-index='perf_scale_ci*' \
  --lookback=15d \
  --output-format=json \
  --save-output-path="results-4.18-controlplane.json"
```

Replace `<your-es-server-url-from-config>` with the `server_url` value from your `~/.orion/elasticsearch-config.yaml`.

### Recommendations for Next Steps

1. **Validate the config:** Run Orion with `--debug` and a short lookback (`--lookback=1d`) first to verify that data is being found and queries are correct.

2. **Tune thresholds:** After initial results, if you see too many false positives, increase thresholds to 20%. If you are missing regressions you know occurred, decrease to 5-8%.

3. **Add more metrics:** Consider expanding this config with:
   - **etcd CPU** (`containerCPU` in `openshift-etcd` namespace) for fuller etcd coverage.
   - **API Server Memory** (`containerMemory` in `openshift-kube-apiserver`) for memory leak detection.
   - **Pod Ready Latency** (`podLatencyQuantilesMeasurement` with `quantileName: Ready`) for user-facing impact.
   - **OVN CPU** (`containerCPU` in `openshift-ovn-kubernetes`) to pair with the memory metric.

4. **Use discovery for validation:** Run the Elasticsearch discovery script to verify that the metric names and namespace labels match your actual data:
   ```bash
   cd ~/.claude/skills/orion-regression-analysis && \
   python3 scripts/discover-es-data.py --config ~/.orion/elasticsearch-config.yaml metrics --benchmark cluster-density-v2
   ```

5. **Set up ACK files:** Once you identify known regressions, create ACK files to suppress them in future runs so new regressions stand out.
