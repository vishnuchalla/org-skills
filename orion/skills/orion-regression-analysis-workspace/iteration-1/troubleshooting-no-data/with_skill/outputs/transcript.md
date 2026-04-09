# Troubleshooting: No Data Returned from Orion with cluster-density and ripsaw-kube-burner-* Index

## User Question

> I'm getting no data returned when I run `orion --config my-config.yaml --hunter-analyze` against my ES cluster. The config has `benchmark.keyword` set to `cluster-density` and I'm using the `ripsaw-kube-burner-*` index. My ES config validates fine. What could be wrong and how do I debug this?

---

## Response

There are several likely causes for the "no data returned" problem here. I will walk through them from most probable to least probable, followed by a systematic debugging approach.

### Most Likely Cause: Wrong Benchmark Name

This is almost certainly your problem. The benchmark name `cluster-density` is **not** a valid benchmark name in the CPT data. The correct name is **`cluster-density-v2`**.

The `benchmark.keyword` field requires an exact, case-sensitive match. Common benchmark names include:

- `cluster-density-v2` (not `cluster-density`)
- `node-density`
- `node-density-cni`
- `node-density-heavy`
- `workers-scale`
- `network-policy`

**Fix:** Change your config from:

```yaml
metadata:
  benchmark.keyword: cluster-density
```

to:

```yaml
metadata:
  benchmark.keyword: cluster-density-v2
```

### Other Possible Causes

If correcting the benchmark name does not resolve the issue, check these additional areas:

#### 1. Metadata Filters Too Restrictive

If your config specifies additional metadata filters (platform, ocpVersion, workerNodesCount, etc.), any of them could be filtering out all data. For example:

```yaml
metadata:
  platform: AWS
  benchmark.keyword: cluster-density-v2
  ocpVersion: "4.22"
  workerNodesCount: 6
  masterNodesType: m6a.xlarge
```

If any one of these values does not match what is actually in your ES data, you will get zero results. To diagnose, **strip your metadata down to just the benchmark filter** and add filters back one at a time:

```yaml
metadata:
  benchmark.keyword: cluster-density-v2
  # Comment out everything else first, then add back one by one
```

#### 2. Lookback Period Too Short or Too Long

If you are not passing a `--lookback` flag, the default may not cover the time range when your data was ingested. Try explicitly setting it:

```bash
orion --config my-config.yaml --hunter-analyze \
  --lookback=30d
```

If you have very recent data, try `--lookback=7d` or even `--lookback=1d` to confirm data exists in a narrow window.

#### 3. Missing Required Command-Line Flags

Orion requires `--es-server`, `--benchmark-index`, and `--metadata-index` flags. Make sure you are providing all of them. A complete command looks like:

```bash
orion --config my-config.yaml --hunter-analyze \
  --es-server='https://your-es-server.com' \
  --benchmark-index='ripsaw-kube-burner-*' \
  --metadata-index='perf_scale_ci*' \
  --lookback=15d
```

Note: the **metadata index** (`perf_scale_ci*`) is separate from the **benchmark index** (`ripsaw-kube-burner-*`). If you are only providing the benchmark index for both, Orion may not find the UUID mappings it needs to correlate metadata with metric data. The metadata index stores the benchmark names, platforms, and versions, while the benchmark index stores the actual metric data.

#### 4. Template Variables Not Provided

If your config uses Jinja2 templating such as:

```yaml
ocpVersion: "{{ version }}"
```

You must pass the variable at runtime:

```bash
orion --config my-config.yaml --hunter-analyze \
  --input-vars='{"version": "4.22"}' \
  ...
```

Without `--input-vars`, the template variable will render as an empty string and match nothing.

#### 5. Index Pattern Mismatch

Verify that the actual index name in your ES cluster matches `ripsaw-kube-burner-*`. Some clusters use slightly different patterns. You can check:

```bash
curl -X GET "https://your-es-server.com/_cat/indices/ripsaw*"
```

### Systematic Debugging Approach

Here is a step-by-step process to isolate the problem:

**Step 1: Enable debug mode**

Add the `--debug` flag to see the exact Elasticsearch queries Orion generates:

```bash
orion --config my-config.yaml --hunter-analyze \
  --es-server='https://your-es-server.com' \
  --benchmark-index='ripsaw-kube-burner-*' \
  --metadata-index='perf_scale_ci*' \
  --lookback=15d \
  --debug
```

The debug output will show:
- The generated ES queries (so you can see exactly what filters are being applied)
- Data processing steps
- Whether UUIDs were found for your metadata filters

**Step 2: Verify the benchmark exists in your data**

Use the discovery script to query your ES cluster for available benchmarks:

```bash
python3 scripts/discover-es-data.py \
  --config ~/.orion/elasticsearch-config.yaml \
  benchmarks
```

This will list all benchmark names with their document counts. Look for the exact name you should be using.

**Step 3: Verify the index has data**

```bash
curl -X GET "https://your-es-server.com/_cat/indices/ripsaw*"
curl -X GET "https://your-es-server.com/_cat/indices/perf_scale*"
```

**Step 4: Test with a minimal config**

Create a bare-minimum config to confirm data flows:

```yaml
tests:
  - name: debug-test
    metadata:
      benchmark.keyword: cluster-density-v2
    metrics:
      - name: simple-test
        metricName: podLatencyQuantilesMeasurement
        quantileName: Ready
        metric_of_interest: P99
```

Run with a broad lookback:

```bash
orion --config debug-config.yaml --hunter-analyze \
  --es-server='https://your-es-server.com' \
  --benchmark-index='ripsaw-kube-burner-*' \
  --metadata-index='perf_scale_ci*' \
  --lookback=30d \
  --debug
```

If this returns data, you know the issue is in your additional metadata filters or metric definitions. Add complexity back incrementally.

**Step 5: Query ES directly**

If the minimal config still returns no data, bypass Orion and query ES directly to confirm data exists:

```bash
curl -s "https://your-es-server.com/perf_scale_ci*/_search" \
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
  }'
```

This will tell you definitively whether benchmark metadata exists and what the exact names are.

### Summary

The most likely fix is changing `cluster-density` to `cluster-density-v2` in your config's `benchmark.keyword` field. If that does not resolve it, work through the debugging steps above -- use `--debug` mode, verify your metadata index is set correctly (`perf_scale_ci*`), and strip your config down to a minimal version to isolate which filter is causing zero matches.
