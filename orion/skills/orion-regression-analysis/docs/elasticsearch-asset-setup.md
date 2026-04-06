# Elasticsearch Asset Setup Guide

This guide walks you through setting up the `elasticsearch-config.yaml` asset for the Orion Claude skill.

## Overview

The Elasticsearch asset replaces environment variables with a centralized, validated configuration approach. It stores your ES connection details, authentication, and preferences in a structured format that Claude can validate and use automatically.

## Quick Setup

### 1. Basic Configuration

The asset template is located at `assets/elasticsearch-config.yaml`. Start by configuring the basic connection:

```yaml
connection:
  server_url: "https://your-opensearch.com"  # Required
  benchmark_index: "ripsaw-kube-burner-*"   # Default index pattern
  metadata_index: "perf_scale_ci*"          # Default metadata pattern
```

### 2. Authentication Setup

Choose your authentication method:

**Option A: No Authentication (Development)**
```yaml
authentication:
  type: "none"
```

**Option B: Basic Authentication**
```yaml
authentication:
  type: "basic"
  username: "your-username"
  password: "your-password"
```

**Option C: API Key Authentication**
```yaml
authentication:
  type: "api_key"
  api_key: "your-api-key"
```

**Option D: Bearer Token**
```yaml
authentication:
  type: "bearer"
  token: "your-bearer-token"
```

### 3. Index Patterns

Customize index patterns to match your Elasticsearch setup:

```yaml
connection:
  benchmark_index: "ripsaw-*"           # For kube-burner performance data
  metadata_index: "perf_scale_ci*"      # For test run metadata
  # or custom patterns:
  # benchmark_index: "my-perf-index-*"
  # metadata_index: "my-metadata-*"
```

### 4. Discovering Your Actual ES Schema

**Important:** Not all Elasticsearch clusters follow the same schema. Before configuring Orion, discover what fields and benchmarks actually exist in your data.

#### Why Schema Discovery Matters

Common schema variations include:
- `jobName.keyword` vs `benchmark.keyword` for benchmark names
- Metadata embedded in documents vs separate indices
- Different field names for timestamps, UUIDs, or metrics
- Nested vs flat document structures

#### Sample Your Data First

Always start by looking at actual documents in your indices:

```bash
# Get a sample document to see the structure
curl -s -u "username:password" \
  "https://your-es-server.com/ripsaw-kube-burner-*/_search" \
  -H "Content-Type: application/json" \
  -d '{"size": 1}' | python3 -m json.tool
```

**What to look for:**
- Where is the benchmark name? (`jobName`, `benchmark`, `workload`, etc.)
- Where is metadata? (nested under `metadata` object or top-level fields?)
- What are the timestamp and UUID fields called?
- How are metrics structured?

#### Discover Available Benchmarks

Find what benchmarks/workloads exist in your data:

```bash
# Try jobName field (common in ripsaw-kube-burner indices)
curl -s -u "username:password" \
  "https://your-es-server.com/ripsaw-kube-burner-*/_search" \
  -H "Content-Type: application/json" \
  -d '{"size": 0, "aggs": {"benchmarks": {"terms": {"field": "jobName.keyword", "size": 50}}}}' \
  | python3 -c "import sys, json; data = json.load(sys.stdin); print('\n'.join([b['key'] for b in data['aggregations']['benchmarks']['buckets']]))"

# Or try benchmark field (common in separate metadata indices)
curl -s -u "username:password" \
  "https://your-es-server.com/perf_scale_ci*/_search" \
  -H "Content-Type: application/json" \
  -d '{"size": 0, "aggs": {"benchmarks": {"terms": {"field": "benchmark.keyword", "size": 50}}}}' \
  | python3 -c "import sys, json; data = json.load(sys.stdin); print('\n'.join([b['key'] for b in data['aggregations']['benchmarks']['buckets']]))"
```

#### Common Schema Patterns

**Pattern 1: Unified Index (No Separate Metadata Index)**
```yaml
# Your data looks like this:
# - Single ripsaw-kube-burner-* index
# - jobName contains benchmark name
# - Metadata nested under "metadata" object

connection:
  benchmark_index: "ripsaw-kube-burner-*"
  metadata_index: "ripsaw-kube-burner-*"  # Same as benchmark!

# When creating Orion configs, use:
metadata:
  jobName.keyword: "cluster-density-v2"  # NOT benchmark.keyword
  metadata.ocpVersion: "4.22"             # Nested metadata path
```

**Pattern 2: Separate Metadata Index**
```yaml
# Your data looks like this:
# - ripsaw-kube-burner-* for metrics
# - perf_scale_ci* for metadata
# - benchmark.keyword contains benchmark name

connection:
  benchmark_index: "ripsaw-kube-burner-*"
  metadata_index: "perf_scale_ci*"       # Separate index

# When creating Orion configs, use:
metadata:
  benchmark.keyword: "cluster-density-v2"  # Standard field
  ocpVersion: "4.22"                       # Top-level metadata
```

#### Update Your Asset Configuration

After discovery, update your asset to reflect the actual schema:

```yaml
data:
  # Adjust field names based on your discovery
  timestamp_field: "@timestamp"  # Or "timestamp", "time", etc.
  uuid_field: "uuid"             # Or "run_id", "testId", etc.
  
# Document your schema notes
notes: |
  Schema discovered on 2026-04-01:
  - Uses jobName.keyword (not benchmark.keyword)
  - Metadata embedded in documents (not separate index)
  - Both indices point to ripsaw-kube-burner-*
```

**Pro tip:** Ask Claude to help with schema discovery! Just say "discover what benchmarks are available" or "sample my ES data structure" and Claude will run these queries for you.

## Detailed Configuration

### Connection Settings

```yaml
connection:
  server_url: "https://your-es-cluster.com"
  benchmark_index: "ripsaw-kube-burner-*"
  metadata_index: "perf_scale_ci*"
  # Optional: Custom port (defaults to 443 for HTTPS)
  # port: 9200
  # Optional: API path prefix
  # path_prefix: "/elasticsearch"
```

### Security Settings

```yaml
settings:
  # SSL/TLS verification
  verify_ssl: true                    # Set to false for self-signed certs
  
  # Request timeout
  timeout: 30                         # Seconds
  
  # Result limits
  max_results: 10000                  # Maximum docs per query
  
  # Optional: Custom CA certificate
  # ca_cert_path: "/path/to/ca.crt"
```

### Data Configuration

```yaml
data:
  # Default lookback period
  default_lookback: "15d"             # Used when not specified in commands
  
  # Field mappings (adjust to your ES schema)
  timestamp_field: "@timestamp"       # Main timestamp field
  uuid_field: "uuid"                  # Test run identifier field
  
  # Global filters applied to all queries
  global_filters:
    # Uncomment and customize for your environment
    # platform: "AWS"
    # clusterType: "self-managed"
    # networkType: "OVNKubernetes"
```

## Validation and Testing

### Automatic Validation

When you configure the asset, Claude will automatically:
1. Validate YAML syntax
2. Test ES connectivity
3. Verify index existence
4. Check authentication

### Manual Testing

Test your configuration manually:

```bash
# Load and validate configuration
source ./scripts/load-es-config.sh validate

# Test basic connectivity
curl -X GET "$ES_SERVER/_cluster/health"

# Check if indices exist
curl -X GET "$ES_SERVER/_cat/indices/${BENCHMARK_INDEX}"
curl -X GET "$ES_SERVER/_cat/indices/${METADATA_INDEX}"
```

## Common Configuration Patterns

### AWS OpenSearch Service

```yaml
connection:
  server_url: "https://search-your-domain.us-east-1.es.amazonaws.com"
  benchmark_index: "ripsaw-*"
  metadata_index: "perf_scale_ci*"

authentication:
  type: "basic"  # or "api_key" for IAM roles
  username: "master-user"
  password: "your-password"

settings:
  verify_ssl: true
  timeout: 60    # AWS can be slower
```

### Elasticsearch Cloud

```yaml
connection:
  server_url: "https://my-deployment.es.cloud.com"
  benchmark_index: "ripsaw-kube-burner-*"
  metadata_index: "perf_scale_ci*"

authentication:
  type: "api_key"
  api_key: "your-cloud-api-key"

settings:
  verify_ssl: true
  timeout: 30
```

### Self-Hosted Cluster

```yaml
connection:
  server_url: "https://elasticsearch.mycompany.com"
  benchmark_index: "openshift-perf-*"
  metadata_index: "test-metadata-*"

authentication:
  type: "basic"
  username: "perf-analyst"
  password: "your-password"

settings:
  verify_ssl: false  # If using self-signed certs
  timeout: 45
  ca_cert_path: "/etc/ssl/certs/company-ca.crt"
```

## Environment-Specific Assets

You can maintain multiple asset files for different environments:

```bash
# Development environment
cp elasticsearch-config.yaml elasticsearch-config-dev.yaml

# Production environment  
cp elasticsearch-config.yaml elasticsearch-config-prod.yaml

# Staging environment
cp elasticsearch-config.yaml elasticsearch-config-staging.yaml
```

Then load the appropriate configuration:
```bash
# Set which asset to use
export ORION_ES_CONFIG="elasticsearch-config-prod.yaml"
```

## Troubleshooting

### Common Issues

**Connection Refused:**
```yaml
# Check server_url format
server_url: "https://your-server.com"  # Include https://
# not: "your-server.com" or "http://your-server.com"
```

**Authentication Failed:**
```yaml
# For API key auth, ensure format is correct
authentication:
  type: "api_key"
  api_key: "base64-encoded-key"  # Not the raw ID:API_KEY
```

**No Data Found:**
```yaml
# Check index patterns match your cluster
connection:
  benchmark_index: "ripsaw-*"      # Use wildcards appropriately
  metadata_index: "perf_scale*"    # Match your naming convention
```

**SSL Certificate Errors:**
```yaml
settings:
  verify_ssl: false               # Temporary fix for dev/staging
  # Better: Add proper CA certificate
  ca_cert_path: "/path/to/ca.pem"
```

### Validation Commands

```bash
# Test asset loading
source ./scripts/load-es-config.sh validate

# Check connectivity
curl -k -X GET "$ES_SERVER/_cluster/health"

# Test authentication
curl -k -u "$ES_USERNAME:$ES_PASSWORD" "$ES_SERVER/_cluster/health"

# Verify index accessibility
curl -k -X GET "$ES_SERVER/${BENCHMARK_INDEX}/_count"
```

## Security Best Practices

### Credential Management

1. **Avoid Hardcoding**: Don't commit passwords in the asset file
2. **Use Environment Variables**: Reference credentials from secure storage
3. **Rotate Keys**: Regularly update API keys and passwords
4. **Principle of Least Privilege**: Grant only necessary ES permissions

### Asset File Security

```bash
# Set appropriate permissions
chmod 600 assets/elasticsearch-config.yaml

# For shared systems, use user-specific configs
cp assets/elasticsearch-config.yaml ~/.orion/elasticsearch-config.yaml
```

### Example with Environment Variable References

```yaml
authentication:
  type: "basic"
  username: "${ES_USERNAME}"        # Reference environment variable
  password: "${ES_PASSWORD}"        # Keep credentials out of file
```

Then set environment variables:
```bash
export ES_USERNAME="your-username"
export ES_PASSWORD="your-password"
```

## Integration with Claude Code

Once configured, the asset integrates seamlessly with Claude:

1. **Automatic Detection**: Claude checks for the asset when Orion tasks are requested
2. **Validation Prompts**: Claude guides you through setup if the asset is missing
3. **Command Generation**: All Orion commands use asset configuration automatically
4. **Troubleshooting**: Claude references asset settings when diagnosing issues

### Example Workflow

```
User: "Help me analyze API server performance regressions"

Claude: 
1. Checks for elasticsearch-config.yaml asset
2. Validates configuration and connectivity
3. Generates appropriate Orion commands using asset settings
4. Provides analysis guidance based on your ES environment
```

This asset-based approach eliminates configuration errors and provides a consistent, validated experience across all Orion interactions.