# Claude Workflow Guide for Orion Skill

This guide helps Claude Code provide the best interactive experience for users.

## Key Principles

1. **Claude IS the wizard** - Don't create bash scripts that duplicate interactive setup
2. **Guide, don't script** - Use conversational flow to gather information
3. **Validate immediately** - Run validation scripts after creating configs
4. **Provide complete commands** - Always give runnable commands with actual values

## User Interaction Patterns

### Pattern 1: First-Time User

**User says**: "Help me with Orion" / "Set up performance analysis"

**Claude should**:
1. Check for existing config at `~/.orion/elasticsearch-config.yaml`
2. If not found: "I'll help you set up Elasticsearch. Do you have access to an ES cluster?"
3. Guide through setup step-by-step (see SKILL.md for details)
4. Use Write tool to create `~/.orion/elasticsearch-config.yaml`
5. Validate with `python3 scripts/validate-es-asset.py`
6. Ask: "Would you like to create your first analysis config?"

**Example conversation flow**:
```
User: Help me set up Orion
Claude: I'll help you configure Orion. First, do you have access to an Elasticsearch cluster with OpenShift performance data?

User: Yes
Claude: Great! What's your Elasticsearch server URL? (include https://)

User: https://my-es.aws.com
Claude: What authentication does it use?
  1. Basic (username/password)
  2. None
  3. API key
  4. Bearer token

User: 1
Claude: What's your username?
...
[After collecting all info]
Claude: Perfect! I'm creating your config at ~/.orion/elasticsearch-config.yaml
[Uses Write tool]
Claude: Validating connection...
[Runs validate-es-asset.py]
Claude: ✓ Connection validated! Would you like to create an analysis config now?
```

### Pattern 2: Create Analysis Config

**User says**: "Create a config for cluster-density on AWS"

**Claude should**:
1. Ask clarifying questions: OCP version? Which components to monitor?
2. Read appropriate example from `docs/examples/`
3. Customize based on user's needs
4. Use Write tool to create config in current directory
5. Explain the config structure
6. Provide complete Orion command to run

**Example**:
```
User: Create a config for cluster-density-v2 on AWS
Claude: I'll create that for you. A few questions:
  - What OCP version? (e.g., 4.22)
  - What components to monitor?
    • Control plane (API server, etcd, OVN)
    • Node resources (kubelet, CRI-O, OVS)
    • Pod lifecycle metrics
    • All of the above

User: 4.22, all of the above
Claude: Perfect! Creating cluster-density-aws-4.22.yaml...
[Uses Write tool with template from docs/examples/basic-cluster-density.yaml]
[Customizes for user's needs]
Claude: ✓ Config created! This monitors:
  - Control plane: API server CPU/mem, etcd latency, OVN performance
  - Node resources: kubelet, CRI-O, OVS metrics
  - Pod metrics: ready/schedule latencies

To run the analysis:
```bash
orion --config cluster-density-aws-4.22.yaml --hunter-analyze \
  --es-server='https://user:pass@my-es.aws.com' \
  --benchmark-index='ripsaw-kube-burner-*' \
  --metadata-index='perf_scale_ci*' \
  --lookback=15d --viz
```
```

### Pattern 3: Troubleshooting

**User says**: "No data found" / "Connection failed" / "How do I interpret this?"

**Claude should**:
1. Validate ES config first
2. Check specific issues based on error
3. Reference `docs/troubleshooting.md`
4. Suggest concrete fixes
5. Re-validate after fixes

## File Creation Guidelines

### When to Use Write Tool

**DO create with Write**:
- `~/.orion/elasticsearch-config.yaml` (user's ES config)
- `<user-chosen-name>.yaml` (analysis configs in current directory)

**DON'T create**:
- `setup-orion.sh` or similar wizard scripts (Claude IS the wizard)
- `create-config.sh` (Claude does this interactively)

### Config File Locations

**Elasticsearch configs**:
- Primary: `~/.orion/elasticsearch-config.yaml` (global user config)
- Alternative: `./orion-es-config.yaml` (project-specific)
- Template: `assets/elasticsearch-config.yaml` (never modify directly)

**Analysis configs**:
- User's current working directory
- Named descriptively: `cluster-density-aws-4.22.yaml`

## Command Generation

### Always Provide Complete Commands

**BAD** (has placeholders):
```bash
orion --config config.yaml --es-server='{{ es_server }}'
```

**GOOD** (runnable):
```bash
orion --config cluster-density-aws-4.22.yaml --hunter-analyze \
  --es-server='https://user:pass@es-server.com' \
  --benchmark-index='ripsaw-kube-burner-*' \
  --metadata-index='perf_scale_ci*' \
  --lookback=15d --viz
```

### Alternative: Use Helper Scripts

If user has configured ES at `~/.orion/elasticsearch-config.yaml`:
```bash
bash scripts/run-analysis.sh cluster-density-aws-4.22.yaml 4.22 hunter-analyze 15d
```

Note: Only suggest helper scripts if the user has already set up ES config AND the scripts have been validated to work.

## Validation Workflow

### After Creating ES Config

Always validate immediately:
```bash
python3 scripts/validate-es-asset.py ~/.orion/elasticsearch-config.yaml
```

If validation fails:
1. Read the error message
2. Suggest fixes (wrong URL? bad credentials? network issue?)
3. Offer to update the config
4. Re-validate

### After Creating Analysis Config

Orion validates configs automatically when you run them - no separate validation needed.

## Common Pitfalls to Avoid

1. **Don't create redundant bash scripts** - Claude handles interaction
2. **Don't use placeholder values** - Generate complete, runnable commands
3. **Don't skip validation** - Always validate after creating configs
4. **Don't assume paths** - Check multiple locations for configs
5. **Don't modify templates** - Copy and customize in user locations
6. **Don't guess benchmark names** - Query ES to discover available benchmarks

## Elasticsearch Discovery Workflows

### Pattern 1: User Doesn't Know Benchmark Name

When Orion returns "No UUID present for given metadata":

1. **Query for available benchmarks**
2. **Show results to user** with run counts
3. **Suggest closest match** based on user's description
4. **Update config** and re-run

Example conversation:
```
User: Create a config for udn-density
Claude: Let me check what's available...
[Runs benchmark discovery]
Claude: I found these UDN-related benchmarks:
  - udn-density-pods (814 runs)
  - virt-udn-density (21 runs)
  
  Based on your request, you likely want "udn-density-pods". 
  Should I create the config with that?
```

### Pattern 2: User Wants to Monitor Component but Doesn't Know Metrics

Help discover what metrics exist:

1. **Ask what component** they want to monitor
2. **Query ES for related metrics**
3. **Show options** with explanations
4. **Create config** with selected metrics

Example conversation:
```
User: I want to monitor OVN performance
Claude: Let me find available OVN metrics...
[Queries for metrics with namespace containing "ovn"]

Found these OVN-related metrics:
  - containerCPU (openshift-ovn-kubernetes) - CPU usage
  - containerMemory (openshift-ovn-kubernetes) - Memory usage
  - ovnControllerCPU - OVN controller specific CPU

Would you like to monitor:
1. All of these (comprehensive monitoring)
2. Just CPU and memory (standard monitoring)
3. Something specific?
```

### Pattern 3: "Metric Not Found" Error

When config validation or Orion fails with missing field:

1. **Sample the metric data** to see actual structure
2. **Show available fields**
3. **Suggest correction**
4. **Update config**

Example conversation:
```
User: My config validation failed - "containerCpu not found"
Claude: Let me check the actual field structure...
[Samples containerCPU data]

I found the issue! The field is "containerCPU" (capital C, capital P), 
not "containerCpu". The data structure shows:
  - metricName: "containerCPU"
  - labels.namespace: "openshift-etcd"
  - value: {"cpu": 5.2}

Should I update your config with the correct field name?
```

## ES Discovery Query Templates

Reference `docs/es-discovery-guide.md` for complete query examples. Key templates:

### Discover Benchmarks
```bash
curl -s -u "$USER:$PASS" "$ES_SERVER/perf_scale_ci*/_search" \
  -H "Content-Type: application/json" \
  -d '{"size": 0, "aggs": {"benchmarks": {"terms": {"field": "benchmark.keyword", "size": 100}}}}'
```

### Discover Metrics for Benchmark
```bash
curl -s -u "$USER:$PASS" "$ES_SERVER/ripsaw-kube-burner-*/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "query": {"term": {"benchmark.keyword": "BENCHMARK_NAME"}},
    "aggs": {"metrics": {"terms": {"field": "metricName.keyword", "size": 200}}}
  }'
```

### Find Namespaces for Metric
```bash
curl -s -u "$USER:$PASS" "$ES_SERVER/ripsaw-kube-burner-*/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "query": {"term": {"metricName.keyword": "METRIC_NAME"}},
    "aggs": {"namespaces": {"terms": {"field": "labels.namespace.keyword", "size": 50}}}
  }'
```

### Sample Metric Data
```bash
curl -s -u "$USER:$PASS" "$ES_SERVER/ripsaw-kube-burner-*/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 1,
    "query": {"term": {"metricName.keyword": "METRIC_NAME"}}
  }' | python3 -m json.tool
```

## When to Use Discovery

**Proactively offer discovery when**:
- User says "I want to monitor X" without specific metrics
- User asks "What metrics are available?"
- Config validation fails with field not found
- Orion returns "No UUID" or "No data found"
- User is creating their first config

**Always format results clearly**:
- Group related items
- Include counts/context
- Highlight recommendations
- Offer next steps

## Quick Reference: File Paths

```
Template (read-only):
  {skill-dir}/assets/elasticsearch-config.yaml
  {skill-dir}/docs/examples/*.yaml

User configs (create here):
  ~/.orion/elasticsearch-config.yaml
  {current-dir}/*.yaml

Validation scripts (call these):
  {skill-dir}/scripts/validate-es-asset.py
  {skill-dir}/scripts/discover-es-data.py
```
