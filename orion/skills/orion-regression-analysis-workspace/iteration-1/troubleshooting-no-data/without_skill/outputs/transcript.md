# Troubleshooting: Orion Returns No Data with `--hunter-analyze`

When Orion returns no data against your Elasticsearch cluster despite a valid ES config, the issue almost always comes down to a mismatch between what your config expects and what actually exists in the index. Here are the most likely causes and how to debug them.

---

## 1. Verify the Exact `benchmark.keyword` Value in Elasticsearch

The most common cause of empty results is that the value you have in your config (`cluster-density`) does not exactly match what is stored in the ES index. Kube-burner workload names have changed over time and across versions. Common variations include:

- `cluster-density` (older)
- `cluster-density-v2` (newer, very common in recent releases)
- `cluster-density-ms` (multi-stream variant)

**How to check:** Query your ES index directly to see what benchmark values actually exist:

```bash
curl -X GET "https://<your-es-host>:9200/ripsaw-kube-burner-*/_search" \
  -H 'Content-Type: application/json' \
  -d '{"size": 0, "aggs": {"benchmarks": {"terms": {"field": "benchmark.keyword", "size": 100}}}}'
```

This will return all distinct `benchmark.keyword` values in the index. Compare these against what you have in your Orion config YAML.

## 2. Check the Index Pattern

The index `ripsaw-kube-burner-*` is the classic Ripsaw/Benchmark Operator index pattern. However, depending on your setup:

- If you are using a newer version of kube-burner or a different indexing pipeline, the index name may differ (e.g., `kube-burner-*` without the `ripsaw-` prefix).
- The index may have a date suffix or rollover alias that does not match the wildcard.

**How to check:** List all indices matching your pattern:

```bash
curl -X GET "https://<your-es-host>:9200/_cat/indices/ripsaw-kube-burner-*?v"
```

If this returns no indices, your index pattern is wrong.

## 3. Check for Time Range / Date Filtering Issues

Orion may be filtering by a time range that excludes your data. Look at your config YAML for any date-related fields such as:

- `start_date` / `end_date`
- `lookback` period
- Any timestamp filters

If your data is older or newer than the configured range, you will get zero results. Try widening or removing any date constraints to see if data appears.

## 4. Verify Additional Filter Fields in Your Config

Orion configs typically include multiple filter dimensions beyond just `benchmark.keyword`. Check whether your YAML specifies filters on fields like:

- `platform.keyword` (e.g., `AWS`, `GCP`, `Azure`)
- `clusterType.keyword`
- `workerNodesCount`
- `masterNodesType.keyword` or `workerNodesType.keyword`
- `ocpVersion`
- `networkType.keyword` (e.g., `OVNKubernetes`, `OpenShiftSDN`)
- `uuid.keyword`

Any of these filters narrowing to a value that does not exist in your data will cause zero results. Verify each filter against what actually exists in the index using an aggregation query similar to the one in step 1.

## 5. Check Metadata vs. Metric Documents

The `ripsaw-kube-burner-*` index may contain different document types -- metadata documents and metric documents. Orion typically needs to match on metadata documents that contain the benchmark information. Make sure:

- The `metricName` or document type field in your config matches what is in the index.
- If there is a `jobConfig.name` or similar nested field, it matches correctly.

## 6. Run Orion with Debug/Verbose Logging

Orion supports increased verbosity. Try running with debug output:

```bash
orion --config my-config.yaml --hunter-analyze --debug
```

or (depending on version):

```bash
orion --config my-config.yaml --hunter-analyze -v
```

This should print the actual Elasticsearch query being constructed. Copy that query and run it directly against your ES cluster with `curl` to see what comes back. This is the single most effective debugging step -- it tells you exactly what Orion is asking for.

## 7. Validate ES Connectivity Beyond Config Validation

Your ES config "validates fine" may mean the connection parameters are correct (host, port, auth), but that does not guarantee:

- The authenticated user/role has read access to the specific index.
- There are no proxy or firewall rules dropping the query payload while allowing the connection.

Check by running a manual search query with the same credentials Orion uses.

## 8. Check Field Mappings

If the `benchmark` field is of type `text` rather than `keyword`, then filtering on `benchmark.keyword` will fail silently (return zero hits). Verify the mapping:

```bash
curl -X GET "https://<your-es-host>:9200/ripsaw-kube-burner-*/_mapping/field/benchmark"
```

You should see a `keyword` sub-field. If the field is mapped differently, you will need to adjust your config or re-index.

---

## Recommended Debugging Sequence

1. **List indices** to confirm the index pattern matches existing indices.
2. **Aggregate on `benchmark.keyword`** to see what values exist.
3. **Run Orion with debug logging** to capture the generated ES query.
4. **Run the generated query manually** via `curl` to isolate whether the problem is in query construction or data.
5. **Remove optional filters one by one** from your config to identify which filter is causing zero results.
6. **Check field mappings** if all values appear correct but results are still empty.

The most likely culprit in your specific case is that the benchmark name stored in your index is `cluster-density-v2` (or another variant) rather than `cluster-density`. The transition to `cluster-density-v2` has been a common source of this exact issue.
