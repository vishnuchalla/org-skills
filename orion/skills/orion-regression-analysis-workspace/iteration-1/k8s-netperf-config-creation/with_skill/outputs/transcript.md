# Orion k8s-netperf Configuration - Transcript

## User Request

> Can you help me set up an Orion config for k8s-netperf analysis? I want to track TCP_STREAM and TCP_RR throughput and latency for pod network (not host network, no service) on AWS with OCP 4.17. I already have my ES connection configured.

## Response

Sure, I can help you set up an Orion configuration for k8s-netperf analysis targeting TCP_STREAM and TCP_RR on pod network for AWS with OCP 4.17.

Since you already have your Elasticsearch connection configured, we can go straight to building the config. There are a few important things to know about k8s-netperf configs that differ from kube-burner configs:

### Key k8s-netperf Configuration Rules

1. **No `aggregation` field** -- k8s-netperf data is pre-aggregated per run, so you must omit any `agg` or `aggregation` fields. Including them would cause empty DataFrames.

2. **Filters go at the metrics level** -- Fields like `profile.keyword`, `hostNetwork`, and `service` must be placed at the **metrics level**, not the metadata level. This is because a single test UUID can contain multiple profiles and scenarios, and filtering at the metrics level lets Orion correctly isolate each combination.

3. **Quoted boolean strings** -- Use `"false"` and `"true"` (quoted strings), not bare YAML booleans `false`/`true`. Bare YAML booleans get capitalized to `False`/`True` which won't match the Elasticsearch data.

4. **Metadata is for UUID matching only** -- The metadata section should contain only `metadata.platform` and `metadata.ocpMajorVersion` for matching test UUIDs.

5. **Same index for benchmark and metadata** -- Unlike kube-burner (which uses separate indices), k8s-netperf stores everything in a single index (`k8s-netperf`), so both `--benchmark-index` and `--metadata-index` should point to `k8s-netperf`.

### Your Configuration

I have created the file `k8s-netperf-aws-417.yaml` with four metrics:

| Metric Name | Profile | Metric of Interest | Threshold | Direction | What It Tracks |
|---|---|---|---|---|---|
| `tcpStreamThroughput` | TCP_STREAM | `throughput` | 10% | -1 (decrease = regression) | Bulk data transfer bandwidth in Mb/s |
| `tcpStreamLatency` | TCP_STREAM | `latency` | 20% | 1 (increase = regression) | Bulk transfer latency in microseconds |
| `tcpRRThroughput` | TCP_RR | `throughput` | 15% | -1 (decrease = regression) | Transaction rate in OP/s |
| `tcpRRLatency` | TCP_RR | `latency` | 20% | 1 (increase = regression) | Round-trip time in microseconds |

All four metrics are filtered to pod network only (`hostNetwork: "false"`, `service: "false"`), matching your requirements.

#### Threshold Rationale

- **TCP_STREAM throughput at 10%**: Stream throughput is relatively stable, so a 10% change is significant and worth flagging.
- **TCP_RR throughput at 15%**: Request-response transaction rates have slightly more variance than bulk streaming, so a slightly wider threshold avoids false positives.
- **Latencies at 20%**: Latency measurements tend to have higher variance, so a 20% threshold provides a good balance between sensitivity and noise reduction.

You can adjust these thresholds based on your environment's baseline stability.

### Running the Analysis

To run the regression analysis with your existing ES configuration:

```bash
orion --config k8s-netperf-aws-417.yaml --hunter-analyze \
  --es-server='<your-es-server-url>' \
  --benchmark-index='k8s-netperf' \
  --metadata-index='k8s-netperf' \
  --lookback=15d --viz
```

Replace `<your-es-server-url>` with your actual Elasticsearch server URL (from your ES config).

The `--hunter-analyze` flag uses Apache Otava-based changepoint detection, which is the recommended algorithm for identifying when performance regressions occurred. The `--viz` flag generates visualizations of the results.

### Optional Enhancements

If you want to expand this configuration later, consider:

- **Adding TCP retransmits** as a reliability indicator for TCP_STREAM (use `metric_of_interest: tcpRetransmits` with `direction: 1` and a 25% threshold).
- **Adding host network baselines** by duplicating the TCP_STREAM/TCP_RR metrics with `hostNetwork: "true"` to compare pod network vs host network performance.
- **Adding service overhead tracking** with `service: "true"` to measure Kubernetes Service routing impact.
- **Increasing lookback** to `30d` or `60d` if you want to capture more historical data for better changepoint detection.
