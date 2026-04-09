#!/usr/bin/env python3
"""Grade all eval outputs against assertions."""
import json
import os
import re
import yaml

BASE = os.path.dirname(os.path.abspath(__file__))


def load_yaml_from_dir(d):
    """Load the first .yaml file found in a directory."""
    for f in os.listdir(d):
        if f.endswith('.yaml'):
            with open(os.path.join(d, f)) as fh:
                return fh.read(), yaml.safe_load(fh.read())
    return None, None


def load_file_content(d, ext):
    """Load file content by extension."""
    for f in os.listdir(d):
        if f.endswith(ext):
            with open(os.path.join(d, f)) as fh:
                return fh.read()
    return ""


def grade_kube_burner(output_dir):
    """Grade kube-burner config creation."""
    yaml_content = load_file_content(output_dir, '.yaml')
    results = []

    # 1. uses-agg-not-aggregation
    has_agg = bool(re.search(r'^\s+agg:\s*$', yaml_content, re.MULTILINE))
    has_aggregation = bool(re.search(r'^\s+aggregation:', yaml_content, re.MULTILINE))
    results.append({
        "text": "uses-agg-not-aggregation",
        "passed": has_agg and not has_aggregation,
        "evidence": f"Found 'agg:': {has_agg}, Found 'aggregation:': {has_aggregation}"
    })

    # 2. agg-has-nested-structure
    has_value = bool(re.search(r'^\s+value:\s+\w+', yaml_content, re.MULTILINE))
    has_agg_type = bool(re.search(r'^\s+agg_type:\s+\w+', yaml_content, re.MULTILINE))
    results.append({
        "text": "agg-has-nested-structure",
        "passed": has_value and has_agg_type,
        "evidence": f"Found nested 'value': {has_value}, Found 'agg_type': {has_agg_type}"
    })

    # 3. includes-metricName
    metric_name_count = len(re.findall(r'^\s+metricName:', yaml_content, re.MULTILINE))
    results.append({
        "text": "includes-metricName",
        "passed": metric_name_count >= 3,
        "evidence": f"Found {metric_name_count} metricName fields (expected >= 3)"
    })

    # 4. includes-node-config
    node_fields = ['masterNodesType', 'masterNodesCount', 'workerNodesType', 'workerNodesCount']
    found = [f for f in node_fields if f in yaml_content]
    results.append({
        "text": "includes-node-config",
        "passed": len(found) == 4,
        "evidence": f"Found {len(found)}/4 node config fields: {found}"
    })

    # 5. correct-namespaces
    has_apiserver_ns = 'openshift-kube-apiserver' in yaml_content
    has_ovn_ns = 'openshift-ovn-kubernetes' in yaml_content
    results.append({
        "text": "correct-namespaces",
        "passed": has_apiserver_ns and has_ovn_ns,
        "evidence": f"openshift-kube-apiserver: {has_apiserver_ns}, openshift-ovn-kubernetes: {has_ovn_ns}"
    })

    # 6. has-benchmark-keyword
    has_bk = bool(re.search(r'benchmark\.keyword:\s*cluster-density-v2', yaml_content))
    results.append({
        "text": "has-benchmark-keyword",
        "passed": has_bk,
        "evidence": f"Found benchmark.keyword: cluster-density-v2: {has_bk}"
    })

    return results


def grade_k8s_netperf(output_dir):
    """Grade k8s-netperf config creation."""
    yaml_content = load_file_content(output_dir, '.yaml')
    results = []

    # 1. no-aggregation-field
    # Check within the metrics section for agg: or aggregation:
    # But we need to be careful - "agg" can appear in comments
    has_agg_field = bool(re.search(r'^\s+(agg|aggregation):\s*$', yaml_content, re.MULTILINE))
    has_agg_type = bool(re.search(r'^\s+agg_type:', yaml_content, re.MULTILINE))
    results.append({
        "text": "no-aggregation-field",
        "passed": not has_agg_field and not has_agg_type,
        "evidence": f"Found 'agg:/aggregation:' block: {has_agg_field}, Found 'agg_type': {has_agg_type}"
    })

    # 2. filters-at-metrics-level
    # profile.keyword, hostNetwork, service should be indented at metrics level (under - name:)
    # not under metadata:
    has_profile_in_metrics = bool(re.search(r'profile\.keyword:', yaml_content))
    has_hostnetwork_in_metrics = bool(re.search(r'hostNetwork:', yaml_content))
    has_service_in_metrics = bool(re.search(r'^\s+service:', yaml_content, re.MULTILINE))
    # Check they're NOT under metadata (ignore comment lines)
    metadata_section = yaml_content.split('metrics:')[0] if 'metrics:' in yaml_content else ""
    # Filter out comment lines before checking
    metadata_lines = [l for l in metadata_section.split('\n') if not l.strip().startswith('#')]
    metadata_no_comments = '\n'.join(metadata_lines)
    filters_in_metadata = ('profile.keyword' in metadata_no_comments or
                          'hostNetwork' in metadata_no_comments or
                          re.search(r'^\s+service:', metadata_no_comments, re.MULTILINE) is not None)
    results.append({
        "text": "filters-at-metrics-level",
        "passed": has_profile_in_metrics and has_hostnetwork_in_metrics and not filters_in_metadata,
        "evidence": f"profile.keyword in metrics: {has_profile_in_metrics}, hostNetwork in metrics: {has_hostnetwork_in_metrics}, filters in metadata: {filters_in_metadata}"
    })

    # 3. quoted-booleans
    # hostNetwork: "false" and service: "false" should use quoted strings
    quoted_false = len(re.findall(r':\s*"false"', yaml_content))
    unquoted_false = len(re.findall(r':\s+false\s*$', yaml_content, re.MULTILINE))
    results.append({
        "text": "quoted-booleans",
        "passed": quoted_false >= 2 and unquoted_false == 0,
        "evidence": f"Quoted 'false' count: {quoted_false}, Unquoted false count: {unquoted_false}"
    })

    # 4. correct-metadata-prefix
    has_metadata_platform = bool(re.search(r'metadata\.platform:', yaml_content))
    has_metadata_version = bool(re.search(r'metadata\.ocpMajorVersion:', yaml_content))
    results.append({
        "text": "correct-metadata-prefix",
        "passed": has_metadata_platform and has_metadata_version,
        "evidence": f"metadata.platform: {has_metadata_platform}, metadata.ocpMajorVersion: {has_metadata_version}"
    })

    # 5. covers-both-profiles
    has_tcp_stream = bool(re.search(r'TCP_STREAM', yaml_content))
    has_tcp_rr = bool(re.search(r'TCP_RR', yaml_content))
    results.append({
        "text": "covers-both-profiles",
        "passed": has_tcp_stream and has_tcp_rr,
        "evidence": f"TCP_STREAM: {has_tcp_stream}, TCP_RR: {has_tcp_rr}"
    })

    return results


def grade_troubleshooting(output_dir):
    """Grade troubleshooting response."""
    transcript = load_file_content(output_dir, '.md')
    results = []

    # 1. identifies-wrong-benchmark-name
    identifies = ('cluster-density-v2' in transcript and
                  ('cluster-density' in transcript) and
                  any(w in transcript.lower() for w in ['wrong', 'incorrect', 'correct name', 'should be', 'not valid', 'not a valid']))
    results.append({
        "text": "identifies-wrong-benchmark-name",
        "passed": identifies,
        "evidence": f"Mentions cluster-density-v2 as correct name: {identifies}"
    })

    # 2. suggests-discovery-script
    suggests_discovery = 'discover-es-data' in transcript or 'discover_es_data' in transcript
    results.append({
        "text": "suggests-discovery-script",
        "passed": suggests_discovery,
        "evidence": f"Mentions discovery script: {suggests_discovery}"
    })

    # 3. suggests-debug-flag
    suggests_debug = '--debug' in transcript
    results.append({
        "text": "suggests-debug-flag",
        "passed": suggests_debug,
        "evidence": f"Mentions --debug flag: {suggests_debug}"
    })

    # 4. mentions-metadata-filters
    mentions_filters = any(phrase in transcript.lower() for phrase in
                          ['metadata filter', 'metadata.', 'too restrictive', 'filter'])
    results.append({
        "text": "mentions-metadata-filters",
        "passed": mentions_filters,
        "evidence": f"Discusses metadata filters: {mentions_filters}"
    })

    return results


def save_grading(eval_dir, variant, results):
    """Save grading results."""
    path = os.path.join(eval_dir, variant, 'grading.json')
    passed = sum(1 for r in results if r['passed'])
    total = len(results)
    data = {
        "pass_rate": passed / total if total > 0 else 0,
        "passed": passed,
        "total": total,
        "expectations": results
    }
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"  {variant}: {passed}/{total} passed ({data['pass_rate']:.0%})")
    return data


# Grade all evals
evals = [
    ("kube-burner-config-creation", grade_kube_burner),
    ("k8s-netperf-config-creation", grade_k8s_netperf),
    ("troubleshooting-no-data", grade_troubleshooting),
]

for eval_name, grader_fn in evals:
    print(f"\n=== {eval_name} ===")
    eval_dir = os.path.join(BASE, eval_name)
    for variant in ['with_skill', 'without_skill']:
        output_dir = os.path.join(eval_dir, variant, 'outputs')
        if os.path.exists(output_dir):
            results = grader_fn(output_dir)
            save_grading(eval_dir, variant, results)
        else:
            print(f"  {variant}: outputs not found")
