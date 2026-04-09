# Orion Config for Control Plane Performance Monitoring

Below is an Orion YAML configuration for monitoring control plane performance during a `cluster-density-v2` workload on AWS with OCP 4.18. This config tracks three key metrics:

- **API Server CPU** - CPU utilization of the kube-apiserver
- **etcd Disk Backend Commit Duration (P99)** - 99th percentile latency for etcd disk commits, a critical indicator of storage performance on the control plane
- **OVN-Kubernetes Memory** - Memory consumption of the OVN-Kubernetes networking components

### Key Configuration Notes

- **`direction: 0`** means Orion will detect regressions in both directions (increases and decreases). Use `1` if you only want to flag increases as regressions, or `-1` for decreases only.
- **`ES_config_path`** points to your existing Elasticsearch configuration at `~/.orion/elasticsearch-config.yaml`.
- **`metadata` filters** ensure Orion queries only results matching your exact cluster topology (3 master + 6 worker m6a.xlarge nodes on AWS with OCP 4.18).
- **`agg_period: 5m`** aggregates metric samples into 5-minute windows before computing the average.

### Running the Analysis

Once saved, you can run Orion against this config:

```bash
orion cmd --config config.yaml
```

To compare against a known-good baseline UUID:

```bash
orion cmd --config config.yaml --baseline <baseline-uuid>
```
