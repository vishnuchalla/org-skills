#!/usr/bin/env python3
"""
Elasticsearch Data Discovery Tool for Orion

Helps you explore your Elasticsearch data to discover available metrics,
benchmarks, fields, and values for creating Orion configurations.

IMPORTANT: The --config flag must come BEFORE the subcommand!

Index Selection:
    The script automatically uses the correct index based on what you're discovering:
    - METADATA queries (benchmarks, platforms, versions) → metadata_index
    - DATA queries (metrics, namespaces, profiles) → benchmark_index

    You can override with --index if needed (e.g., for k8s-netperf data)

Field Priority:
    The script intelligently tries different benchmark field names based on index type:
    - Metadata indexes (perf_scale_ci*) → benchmark.keyword → benchmark → jobName
    - Benchmark indexes (ripsaw-kube-burner-*) → jobName → benchmark.keyword → benchmark

    This ensures efficient discovery regardless of your data schema!

Usage:
    # Discover available benchmarks
    python3 discover-es-data.py --config ~/.orion/elasticsearch-config.yaml benchmarks

    # Discover metrics for a benchmark
    python3 discover-es-data.py --config ~/.orion/elasticsearch-config.yaml metrics --benchmark cluster-density-v2

    # Find namespaces for a metric
    python3 discover-es-data.py --config ~/.orion/elasticsearch-config.yaml namespaces --metric containerCPU

    # Get sample document structure
    python3 discover-es-data.py --config ~/.orion/elasticsearch-config.yaml sample --benchmark cluster-density-v2

    # Discover available platforms
    python3 discover-es-data.py --config ~/.orion/elasticsearch-config.yaml platforms

    # Discover OCP versions
    python3 discover-es-data.py --config ~/.orion/elasticsearch-config.yaml versions --benchmark cluster-density-v2

    # Discover node configuration (counts and instance types)
    python3 discover-es-data.py --config ~/.orion/elasticsearch-config.yaml node-config

    # Discover node configuration for specific benchmark
    python3 discover-es-data.py --config ~/.orion/elasticsearch-config.yaml node-config --benchmark cluster-density-v2

For k8s-netperf (use --index flag to override - note: single index, not pattern):
    # List test profiles
    python3 discover-es-data.py --config ~/.orion/elasticsearch-config.yaml --index k8s-netperf profiles

    # List test scenarios
    python3 discover-es-data.py --config ~/.orion/elasticsearch-config.yaml --index k8s-netperf scenarios --profile TCP_STREAM

    # Discover benchmarks/jobNames
    python3 discover-es-data.py --config ~/.orion/elasticsearch-config.yaml --index k8s-netperf benchmarks

    # Get sample document
    python3 discover-es-data.py --config ~/.orion/elasticsearch-config.yaml --index k8s-netperf sample

Default config location: ~/.orion/elasticsearch-config.yaml (used if --config is omitted)
"""

import argparse
import yaml
import sys
from urllib.parse import urlparse
from opensearchpy import OpenSearch
from opensearchpy.exceptions import ConnectionError, AuthenticationException
import json

def load_config(config_path):
    """Load ES configuration from elasticsearch-config.yaml"""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"Error loading config from {config_path}: {e}", file=sys.stderr)
        sys.exit(1)

def create_es_client(config):
    """Create OpenSearch/Elasticsearch client from config"""
    conn = config['connection']
    auth = config['authentication']
    settings = config.get('settings', {})

    # Parse server URL
    url = conn['server_url']
    parsed = urlparse(url)

    # Build auth
    http_auth = None
    headers = {}

    if auth['type'] == 'basic':
        http_auth = (auth['username'], auth['password'])
    elif auth['type'] == 'api_key':
        headers['x-api-key'] = auth['api_key']
    elif auth['type'] == 'bearer':
        headers['Authorization'] = f"Bearer {auth['token']}"

    # Create client
    es = OpenSearch(
        [url],
        http_auth=http_auth,
        headers=headers if headers else None,
        use_ssl=True,
        verify_certs=settings.get('verify_ssl', True),
        timeout=settings.get('timeout', 30)
    )

    return es

def get_benchmark_field_priority(index):
    """
    Determine field priority based on index pattern.

    Metadata indexes (perf_scale_ci*) use benchmark.keyword
    Benchmark/data indexes (ripsaw-kube-burner-*, k8s-netperf-*) use jobName
    """
    index_lower = index.lower()

    # Check if this is a metadata index
    if 'perf_scale_ci' in index_lower or 'metadata' in index_lower:
        # Metadata index - benchmark fields first
        return [
            ("benchmark.keyword", "benchmark.keyword"),
            ("benchmark", "benchmark"),
            ("jobName.keyword", "jobName")
        ]
    else:
        # Benchmark/data index - jobName first
        return [
            ("jobName.keyword", "jobName"),
            ("benchmark.keyword", "benchmark.keyword"),
            ("benchmark", "benchmark")
        ]

def discover_benchmarks(es, index):
    """Discover available benchmarks - smart field priority based on index type"""
    # Get field priority based on index pattern
    fields_to_try = get_benchmark_field_priority(index)

    benchmarks = None
    field_used = None
    total_docs = 0

    # Show which field order we're trying
    field_order = " → ".join([f[1] for f in fields_to_try])

    for field, display_name in fields_to_try:
        query = {
            "size": 0,
            "aggs": {
                "benchmarks": {
                    "terms": {
                        "field": field,
                        "size": 100
                    }
                }
            }
        }

        try:
            result = es.search(index=index, body=query)
            total_docs = result['hits']['total']['value'] if isinstance(result['hits']['total'], dict) else result['hits']['total']
            benchmarks = result['aggregations']['benchmarks']['buckets']

            if benchmarks:
                field_used = display_name
                break
        except Exception as e:
            # Field doesn't exist, try next one
            continue

    print(f"\n🔍 Searching index: {index}")
    print(f"📊 Total documents: {total_docs}")
    print(f"🎯 Field priority: {field_order}")

    if field_used:
        print(f"🔑 Using field: {field_used}")

    print("\nAvailable Benchmarks:")
    print("=" * 70)

    if not benchmarks:
        print("\n⚠️  No benchmarks found!")
        print("\nPossible reasons:")
        print("  • Index pattern doesn't match any indices")
        print("  • No documents in the matched indices")
        print(f"  • None of these fields exist (tried in order: {field_order})")
        print("\nTry running 'sample' command to see document structure")
        return

    for b in sorted(benchmarks, key=lambda x: x['doc_count'], reverse=True):
        print(f"{b['key']:50} {b['doc_count']:>8} runs")
    print(f"\n✓ Total: {len(benchmarks)} benchmarks")

def discover_metrics(es, index, benchmark):
    """Discover available metrics for a benchmark - smart field priority based on index type"""
    # Get field priority based on index pattern
    field_tuples = get_benchmark_field_priority(index)
    fields_to_try = [f[0] for f in field_tuples]
    field_order = " → ".join([f[1] for f in field_tuples])

    doc_count = 0
    metrics = None
    field_used = None

    for field in fields_to_try:
        query = {
            "size": 0,
            "query": {
                "term": {field: benchmark}
            },
            "aggs": {
                "metrics": {
                    "terms": {
                        "field": "metricName.keyword",
                        "size": 200
                    }
                }
            }
        }

        try:
            result = es.search(index=index, body=query)
            doc_count = result['hits']['total']['value'] if isinstance(result['hits']['total'], dict) else result['hits']['total']

            if doc_count > 0:
                field_used = field
                metrics = result['aggregations']['metrics']['buckets']
                break
        except Exception:
            continue

    print(f"\n🔍 Searching index: {index}")
    print(f"📊 Documents for benchmark '{benchmark}': {doc_count}")
    print(f"🎯 Field priority: {field_order}")
    if field_used:
        print(f"🔑 Using field: {field_used}")

    if doc_count == 0:
        print(f"\n⚠️  No documents found for benchmark '{benchmark}'")
        print("\nPossible reasons:")
        print("  • Benchmark name is incorrect (case-sensitive)")
        print("  • No data exists for this benchmark")
        print(f"  • Tried fields in this order: {field_order}")
        print(f"  • None of them contain '{benchmark}'")
        print("\nTry running: discover-es-data.py benchmarks")
        return

    if metrics:
        print(f"\nAvailable Metrics for '{benchmark}':")
        print("=" * 70)
        for m in sorted(metrics, key=lambda x: x['doc_count'], reverse=True):
            print(f"{m['key']:60} {m['doc_count']:>10}")
        print(f"\n✓ Total: {len(metrics)} metrics")
    else:
        print(f"\n⚠️  No metricName field found (might be k8s-netperf or different structure)")
        print("\nTry using: discover-es-data.py sample --benchmark", benchmark)

def discover_namespaces(es, index, metric):
    """Discover available namespaces for a metric"""
    query = {
        "size": 0,
        "query": {
            "term": {"metricName.keyword": metric}
        },
        "aggs": {
            "namespaces": {
                "terms": {
                    "field": "labels.namespace.keyword",
                    "size": 100
                }
            }
        }
    }

    result = es.search(index=index, body=query)
    doc_count = result['hits']['total']['value'] if isinstance(result['hits']['total'], dict) else result['hits']['total']
    namespaces = result['aggregations']['namespaces']['buckets']

    print(f"\n🔍 Searching index: {index}")
    print(f"📊 Documents for metric '{metric}': {doc_count}")

    if doc_count == 0:
        print(f"\n⚠️  No documents found for metric '{metric}'")
        print("\nPossible reasons:")
        print("  • Metric name is incorrect (case-sensitive)")
        print("  • No data exists for this metric")
        print("\nTry running: discover-es-data.py metrics --benchmark <benchmark-name>")
        return

    if namespaces:
        print(f"\nNamespaces with '{metric}' data:")
        print("=" * 70)
        for ns in namespaces:
            if ns['key']:  # Skip empty
                print(f"{ns['key']:55} {ns['doc_count']:>8} samples")
        print(f"\n✓ Total: {len([n for n in namespaces if n['key']])} namespaces")
    else:
        print(f"\n⚠️  No namespace labels found for metric '{metric}'")

def discover_platforms(es, index):
    """Discover available platforms"""
    # Try both top-level and nested metadata
    for field in ["platform.keyword", "metadata.platform.keyword"]:
        query = {
            "size": 0,
            "aggs": {
                "platforms": {
                    "terms": {
                        "field": field,
                        "size": 50
                    }
                }
            }
        }

        try:
            result = es.search(index=index, body=query)
            platforms = result['aggregations']['platforms']['buckets']

            if platforms:
                print(f"\nAvailable Platforms (field: {field}):")
                print("=" * 70)
                for p in sorted(platforms, key=lambda x: x['doc_count'], reverse=True):
                    print(f"{p['key']:30} {p['doc_count']:>8} runs")
                print(f"\nTotal: {len(platforms)} platforms")
                return
        except:
            continue

    print("\nNo platform field found")

def discover_versions(es, index, benchmark=None):
    """Discover available OCP versions - smart field priority based on index type"""
    # Try different version field patterns
    version_fields = [
        "ocpVersion.keyword",
        "metadata.ocpVersion.keyword",
        "metadata.ocpMajorVersion.keyword"
    ]

    # Get benchmark field priority based on index pattern
    benchmark_fields = [f[0] for f in get_benchmark_field_priority(index)]

    for field in version_fields:
        query = {
            "size": 0,
            "aggs": {
                "versions": {
                    "terms": {
                        "field": field,
                        "size": 100
                    }
                }
            }
        }

        # If benchmark filter provided, try both field patterns
        if benchmark:
            found_versions = False
            for bench_field in benchmark_fields:
                query["query"] = {"term": {bench_field: benchmark}}
                try:
                    result = es.search(index=index, body=query)
                    versions = result['aggregations']['versions']['buckets']
                    if versions:
                        found_versions = True
                        print(f"\nOCP Versions (field: {field}, filtered by {bench_field}: {benchmark}):")
                        print("=" * 70)
                        for v in sorted(versions, key=lambda x: x['key'], reverse=True)[:30]:
                            print(f"{v['key']:50} {v['doc_count']:>6} runs")
                        print(f"\nTotal: {len(versions)} versions")
                        return
                except:
                    continue
            if found_versions:
                return
            continue

        try:
            result = es.search(index=index, body=query)
            versions = result['aggregations']['versions']['buckets']

            if versions:
                print(f"\nOCP Versions (field: {field}):")
                print("=" * 70)
                # Sort by version (reverse)
                for v in sorted(versions, key=lambda x: x['key'], reverse=True)[:30]:
                    print(f"{v['key']:50} {v['doc_count']:>6} runs")
                print(f"\nTotal: {len(versions)} versions")
                return
        except:
            continue

    print("\nNo version fields found")

def sample_document(es, index, benchmark=None, profile=None):
    """Get sample document to see structure - smart field priority based on index type"""
    result = None
    filters_desc = []
    field_used = None

    # Show header first
    print(f"\n🔍 Searching index: {index}")

    # If benchmark filter provided, get field priority based on index
    if benchmark:
        field_tuples = get_benchmark_field_priority(index)
        benchmark_fields = [f[0] for f in field_tuples]
        field_order = " → ".join([f[1] for f in field_tuples])

        print(f"🎯 Field priority: {field_order}")

        for bench_field in benchmark_fields:
            query = {"size": 1}

            # Build query with benchmark filter
            if profile:
                query["query"] = {
                    "bool": {
                        "must": [
                            {"term": {bench_field: benchmark}},
                            {"term": {"profile.keyword": profile}}
                        ]
                    }
                }
            else:
                query["query"] = {"term": {bench_field: benchmark}}

            try:
                result = es.search(index=index, body=query)
                if result['hits']['hits']:
                    field_used = bench_field
                    filters_desc.append(f"{bench_field}='{benchmark}'")
                    if profile:
                        filters_desc.append(f"profile='{profile}'")
                    break
            except:
                continue

        if not result or not result['hits']['hits']:
            # No results with benchmark filter
            print(f"   Tried fields: {field_order}")
            print(f"   Looking for: {benchmark}" + (f" with profile={profile}" if profile else ""))
            print("\n⚠️  No documents found")
            print(f"\nPossible reasons:")
            print(f"  • No documents match '{benchmark}' in any of these fields")
            print(f"  • Benchmark name is incorrect (case-sensitive)")
            print("\nTry running: discover-es-data.py benchmarks")
            return

        # Show which field worked
        print(f"🔑 Using field: {field_used}")
        if filters_desc:
            print(f"   Filters: {', '.join(filters_desc)}")
    else:
        # No benchmark filter, just get any document
        query = {"size": 1}
        if profile:
            query["query"] = {"term": {"profile.keyword": profile}}
            filters_desc.append(f"profile='{profile}'")

        result = es.search(index=index, body=query)

        if filters_desc:
            print(f"   Filters: {', '.join(filters_desc)}")

    if result and result['hits']['hits']:
        doc = result['hits']['hits'][0]['_source']
        print(f"\n📄 Sample Document Structure:")
        print("=" * 70)
        print(json.dumps(doc, indent=2, default=str))
    else:
        print("\n⚠️  No documents found")

def discover_profiles(es, index):
    """Discover k8s-netperf test profiles"""
    query = {
        "size": 0,
        "aggs": {
            "profiles": {
                "terms": {
                    "field": "profile.keyword",
                    "size": 50
                }
            }
        }
    }

    result = es.search(index=index, body=query)
    profiles = result['aggregations']['profiles']['buckets']

    if profiles:
        print(f"\nAvailable Test Profiles:")
        print("=" * 70)
        for p in profiles:
            print(f"{p['key']:40} {p['doc_count']:>8} tests")
        print(f"\nTotal: {len(profiles)} profiles")
    else:
        print("\nNo profile field found (not k8s-netperf data)")

def discover_node_config(es, index, benchmark=None):
    """Discover node counts and instance types - optionally filter by benchmark"""
    # Fields to discover
    node_fields = {
        'counts': [
            'masterNodesCount',
            'workerNodesCount',
            'infraNodesCount'
        ],
        'types': [
            'masterNodesType.keyword',
            'workerNodesType.keyword',
            'infraNodesType.keyword',
            'masterInstanceType.keyword',
            'workerInstanceType.keyword',
            'masterNodesType',  # Try without keyword too
            'workerNodesType'
        ]
    }

    print(f"\n🔍 Searching index: {index}")

    # Prepare base query filter for benchmark if provided
    base_query_filter = None
    if benchmark:
        # Use smart field priority for benchmark filtering
        field_tuples = get_benchmark_field_priority(index)
        benchmark_fields = [f[0] for f in field_tuples]
        field_order = " → ".join([f[1] for f in field_tuples])

        print(f"🎯 Field priority: {field_order}")
        print(f"📌 Filtering by benchmark: {benchmark}")

        # Try to find which field has data for this benchmark
        for bench_field in benchmark_fields:
            test_query = {
                "size": 0,
                "query": {"term": {bench_field: benchmark}}
            }
            try:
                test_result = es.search(index=index, body=test_query)
                doc_count = test_result['hits']['total']['value'] if isinstance(test_result['hits']['total'], dict) else test_result['hits']['total']
                if doc_count > 0:
                    base_query_filter = {"term": {bench_field: benchmark}}
                    print(f"🔑 Using field: {bench_field}")
                    print(f"📊 Total runs for '{benchmark}': {doc_count}")
                    break
            except:
                continue

        if not base_query_filter:
            print(f"\n⚠️  No documents found for benchmark '{benchmark}'")
            print(f"   Tried fields: {field_order}")
            print("\nTry running: discover-es-data.py benchmarks")
            return

    # First, discover platforms to determine if baremetal
    platform_query = {
        "size": 0,
        "aggs": {
            "platforms": {
                "terms": {
                    "field": "platform",
                    "size": 20
                }
            }
        }
    }

    # Add benchmark filter if provided
    if base_query_filter:
        platform_query["query"] = base_query_filter

    try:
        result = es.search(index=index, body=platform_query)
        platforms = result['aggregations']['platforms']['buckets']
        has_baremetal = any('bare' in p['key'].lower() or 'metal' in p['key'].lower() for p in platforms)

        print(f"\n📊 Platforms found: {', '.join([p['key'] for p in platforms])}")
        if has_baremetal:
            print("   ⚠️  Baremetal detected - instance types not applicable")
    except:
        has_baremetal = False

    # Discover node counts
    print(f"\n🔢 Node Counts:")
    print("=" * 70)

    for field in node_fields['counts']:
        query = {
            "size": 0,
            "aggs": {
                "values": {
                    "terms": {
                        "field": field,
                        "size": 50
                    }
                }
            }
        }

        # Add benchmark filter if provided
        if base_query_filter:
            query["query"] = base_query_filter

        try:
            result = es.search(index=index, body=query)
            values = result['aggregations']['values']['buckets']
            if values:
                value_list = ', '.join([f"{v['key']} ({v['doc_count']} runs)" for v in sorted(values, key=lambda x: x['key'])])
                print(f"  {field:25} {value_list}")
        except:
            continue

    # Discover instance types (skip if baremetal only)
    if not has_baremetal or any('aws' in p['key'].lower() or 'gcp' in p['key'].lower() or 'azure' in p['key'].lower() for p in platforms):
        print(f"\n🖥️  Instance Types:")
        print("=" * 70)

        for field in node_fields['types']:
            query = {
                "size": 0,
                "aggs": {
                    "types": {
                        "terms": {
                            "field": field,
                            "size": 50
                        }
                    }
                }
            }

            # Add benchmark filter if provided
            if base_query_filter:
                query["query"] = base_query_filter

            try:
                result = es.search(index=index, body=query)
                types = result['aggregations']['types']['buckets']
                if types:
                    type_list = ', '.join([f"{t['key']} ({t['doc_count']} runs)" for t in sorted(types, key=lambda x: x['doc_count'], reverse=True)[:10]])
                    print(f"  {field:25} {type_list}")
            except:
                continue

        # Show correlations: count + type combinations
        print(f"\n🔗 Count + Type Correlations:")
        print("=" * 70)

        correlations = [
            ('masterNodesCount', 'masterNodesType.keyword', 'Master Nodes'),
            ('workerNodesCount', 'workerNodesType.keyword', 'Worker Nodes'),
            ('infraNodesCount', 'infraNodesType.keyword', 'Infra Nodes')
        ]

        for count_field, type_field, label in correlations:
            query = {
                "size": 0,
                "aggs": {
                    "combinations": {
                        "multi_terms": {
                            "terms": [
                                {"field": count_field},
                                {"field": type_field}
                            ],
                            "size": 50,
                            "order": {"_count": "desc"}
                        }
                    }
                }
            }

            # Add benchmark filter if provided
            if base_query_filter:
                query["query"] = base_query_filter

            try:
                result = es.search(index=index, body=query)
                combos = result['aggregations']['combinations']['buckets']
                if combos:
                    print(f"\n  {label}:")
                    for combo in combos[:15]:  # Show top 15 combinations
                        count = combo['key'][0]
                        instance_type = combo['key'][1]
                        runs = combo['doc_count']
                        if instance_type:  # Skip empty types
                            print(f"    {count:>4} × {instance_type:35} ({runs:>4} runs)")
            except Exception as e:
                # multi_terms might not be supported in older ES versions
                continue
    else:
        print(f"\n⚠️  Skipping instance types (baremetal platform)")

def discover_scenarios(es, index, profile=None):
    """Discover k8s-netperf test scenarios"""
    query = {
        "size": 0,
        "aggs": {
            "scenarios": {
                "multi_terms": {
                    "terms": [
                        {"field": "hostNetwork"},
                        {"field": "service"},
                        {"field": "local"}
                    ],
                    "size": 50
                }
            }
        }
    }

    if profile:
        query["query"] = {"term": {"profile.keyword": profile}}

    try:
        result = es.search(index=index, body=query)
        scenarios = result['aggregations']['scenarios']['buckets']

        if scenarios:
            print(f"\nTest Scenarios (hostNetwork, service, local):")
            print("=" * 70)
            for s in sorted(scenarios, key=lambda x: x['doc_count'], reverse=True):
                keys = s['key']
                host = 'hostNetwork' if keys[0] else 'podNetwork'
                svc = 'service' if keys[1] else 'direct'
                loc = 'sameNode' if keys[2] else 'crossNode'
                print(f"{host:15} {svc:10} {loc:12} {s['doc_count']:>6} tests")
        else:
            print("\nNo scenario fields found")
    except Exception as e:
        print(f"\nError discovering scenarios: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Discover data in Elasticsearch for Orion configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--config',
        default='~/.orion/elasticsearch-config.yaml',
        help='Path to elasticsearch-config.yaml (default: ~/.orion/elasticsearch-config.yaml)'
    )

    parser.add_argument(
        '--index',
        help='Override index pattern (e.g., k8s-netperf-*). By default, metadata commands use metadata_index, data commands use benchmark_index.'
    )

    parser.add_argument(
        '--use-benchmark-index',
        action='store_true',
        help='Force use of benchmark_index instead of metadata_index (for debugging)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Discovery command')

    # Benchmarks
    subparsers.add_parser('benchmarks', help='List available benchmarks')

    # Metrics
    metrics_parser = subparsers.add_parser('metrics', help='List metrics for a benchmark')
    metrics_parser.add_argument('--benchmark', required=True, help='Benchmark name')

    # Namespaces
    ns_parser = subparsers.add_parser('namespaces', help='List namespaces for a metric')
    ns_parser.add_argument('--metric', required=True, help='Metric name')

    # Platforms
    subparsers.add_parser('platforms', help='List available platforms')

    # Node configuration
    node_config_parser = subparsers.add_parser('node-config', help='List node counts and instance types')
    node_config_parser.add_argument('--benchmark', help='Filter by benchmark')

    # Versions
    versions_parser = subparsers.add_parser('versions', help='List OCP versions')
    versions_parser.add_argument('--benchmark', help='Filter by benchmark')

    # Sample
    sample_parser = subparsers.add_parser('sample', help='Get sample document structure')
    sample_parser.add_argument('--benchmark', help='Filter by benchmark')
    sample_parser.add_argument('--profile', help='Filter by profile (k8s-netperf)')

    # k8s-netperf specific
    subparsers.add_parser('profiles', help='List k8s-netperf test profiles')

    scenarios_parser = subparsers.add_parser('scenarios', help='List k8s-netperf test scenarios')
    scenarios_parser.add_argument('--profile', help='Filter by profile')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Load config
    import os
    config_path = os.path.expanduser(args.config)
    config = load_config(config_path)

    # Create ES client
    try:
        es = create_es_client(config)
        # Test connection
        info = es.info()
        print(f"\n✓ Connected to: {config['connection']['server_url']}")
        print(f"  Cluster: {info.get('cluster_name', 'unknown')}")
        print(f"  Version: {info.get('version', {}).get('number', 'unknown')}")
    except (ConnectionError, AuthenticationException) as e:
        print(f"\n✗ Error connecting to Elasticsearch: {e}", file=sys.stderr)
        print(f"\nConnection details from config:")
        print(f"  Server: {config['connection']['server_url']}")
        print(f"  Auth type: {config['authentication']['type']}")
        sys.exit(1)

    # Determine index based on command type
    # Metadata queries use metadata_index, data queries use benchmark_index
    metadata_commands = ['benchmarks', 'platforms', 'versions', 'node-config']

    if args.index:
        # User override
        index = args.index
        print(f"📌 Using override index: {index}")
    elif args.use_benchmark_index:
        # Force benchmark index
        index = config['connection']['benchmark_index']
        print(f"📌 Forcing benchmark index: {index}")
    elif args.command in metadata_commands:
        # Use metadata index for benchmark/platform/version discovery
        index = config['connection']['metadata_index']
        print(f"📊 Using metadata index: {index}")
    else:
        # Use benchmark index for metrics/namespaces/samples/profiles
        index = config['connection']['benchmark_index']
        print(f"📈 Using benchmark index: {index}")

    # Execute command
    try:
        if args.command == 'benchmarks':
            discover_benchmarks(es, index)
        elif args.command == 'metrics':
            discover_metrics(es, index, args.benchmark)
        elif args.command == 'namespaces':
            discover_namespaces(es, index, args.metric)
        elif args.command == 'platforms':
            discover_platforms(es, index)
        elif args.command == 'node-config':
            discover_node_config(es, index, getattr(args, 'benchmark', None))
        elif args.command == 'versions':
            discover_versions(es, index, getattr(args, 'benchmark', None))
        elif args.command == 'sample':
            sample_document(es, index, getattr(args, 'benchmark', None), getattr(args, 'profile', None))
        elif args.command == 'profiles':
            discover_profiles(es, index)
        elif args.command == 'scenarios':
            discover_scenarios(es, index, getattr(args, 'profile', None))
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
