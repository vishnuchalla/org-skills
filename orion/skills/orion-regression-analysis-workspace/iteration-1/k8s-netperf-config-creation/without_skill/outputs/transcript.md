# Orion Config for k8s-netperf Analysis

Here is an Orion YAML configuration for tracking TCP_STREAM and TCP_RR performance metrics on a pod-to-pod (no hostNetwork, no service) network path, targeting AWS with OCP 4.17.

### Key notes on this configuration

- **`direction: 1`** means higher is better (throughput) while **`direction: -1`** means lower is better (latency).
- The **`metadata`** filters ensure you only match pod-network runs (`hostNetwork: false`, `service: false`) on AWS with OCP 4.17.
- **`max_regression: 5`** sets a 5% threshold for flagging regressions; **`max_progression: 50`** allows up to 50% improvement before flagging as unusual.
- The `ES_SERVER` and `ES_INDEX` environment variables are referenced since you mentioned your ES connection is already configured.
- The `index` and `benchmarkIndex` fields point to the `k8s-netperf` Elasticsearch index where your netperf results are stored.
- You may need to adjust the `metricField` names (e.g., `throughput`, `latency`) to match the exact field names in your Elasticsearch index schema.

To run this config with Orion:

```bash
orion cmd --config config.yaml
```
