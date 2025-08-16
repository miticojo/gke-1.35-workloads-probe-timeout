# GKE 1.35 Workloads Probe Timeout Monitor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Kubernetes](https://img.shields.io/badge/kubernetes-%3E%3D1.20-blue)](https://kubernetes.io/)
[![GKE](https://img.shields.io/badge/GKE-1.35%20Ready-green)](https://cloud.google.com/kubernetes-engine)

A comprehensive solution for monitoring and remediating Kubernetes exec probe timeouts in preparation for GKE 1.35's ExecProbeTimeout enforcement.

## 🚨 The Problem

Starting with GKE version 1.35, Kubernetes will strictly enforce the `timeoutSeconds` configuration for exec probes (liveness, readiness, and startup). Previously, this timeout was not enforced in GKE, meaning probes that took longer than the configured timeout would still be considered successful.

### What's Changing?
- **Before GKE 1.35**: `timeoutSeconds` on exec probes was ignored
- **After GKE 1.35**: Probes exceeding `timeoutSeconds` will be marked as failed
- **Default timeout**: 1 second (if not explicitly configured)

### Impact
- Pods may restart unexpectedly if liveness probes exceed timeout
- Services may lose endpoints if readiness probes exceed timeout  
- Applications may fail to start if startup probes exceed timeout

## 🎯 The Solution

This repository provides a **non-invasive monitoring solution** that:
1. **Discovers** all workloads using exec probes
2. **Monitors** actual probe execution times without modifying workloads
3. **Analyzes** metrics to recommend appropriate timeout values
4. **Remediates** by generating patches with optimal configurations

## 📊 Architecture

```
DaemonSet Exporter → Prometheus → Analysis Script → Recommendations → Patches
                          ↓
                  Cloud Monitoring Dashboard
```

## 🚀 Quick Start

### Prerequisites
- Kubernetes cluster (GKE or any K8s >= 1.20)
- kubectl configured with cluster access
- Prometheus (or Google Managed Prometheus in GKE)
- Python 3.8+ (for analysis scripts)

### Step 1: Deploy the Monitoring Stack

```bash
# Deploy the probe metrics exporter DaemonSet
kubectl apply -f monitoring/probe-metrics-exporter.yaml

# Verify deployment
kubectl get pods -n probe-monitoring
```

### Step 2: Wait for Metrics Collection

Allow 24-48 hours for meaningful data collection. The exporter will:
- Monitor kubelet logs for probe execution patterns
- Export metrics to Prometheus
- Track timeout violations in real-time

### Step 3: Analyze Metrics

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run analysis (Prometheus)
python scripts/analyze-prometheus-metrics.py \
  --prometheus-url http://prometheus:9090

# Or use Google Cloud Monitoring
python scripts/analyze-prometheus-metrics.py \
  --cloud-monitoring
```

### Step 4: Review Recommendations

The analysis generates:
- `prometheus-probe-analysis-{timestamp}.json` - Detailed analysis
- `apply-patches-{timestamp}.sh` - Ready-to-run patch script

Example output:
```
📊 SUMMARY
  Total probes needing attention: 23
  High impact (>50% violations): 3
  Medium impact (10-50% violations): 8
  Low impact (<10% violations): 12

🚨 TOP CRITICAL WORKLOADS
1. production/api-server
   P99 Duration: 2.3s
   Violation Rate: 78%
   Recommended timeoutSeconds: 3
```

### Step 5: Apply Remediations

```bash
# Review the generated patches
cat apply-patches-*.sh

# Apply patches (dry-run first)
./apply-patches-{timestamp}.sh --dry-run

# Apply patches
./apply-patches-{timestamp}.sh
```

## 📈 Monitoring Dashboard

### Prometheus Queries

Key metrics to monitor:

```promql
# P99 probe duration
histogram_quantile(0.99,
  sum(rate(kubernetes_probe_duration_seconds_bucket[24h])) 
  by (namespace, pod, probe_type, le)
)

# Timeout violation rate
sum(rate(kubernetes_probe_timeout_violations_total[1h])) 
by (namespace, pod, container, probe_type)
```

### Google Cloud Monitoring

Import the dashboard:
```bash
gcloud monitoring dashboards create \
  --config-from-file=monitoring/cloud-monitoring-dashboard.json
```

## 🛠️ Alternative Solutions

### Quick Audit (No Monitoring Required)

For immediate assessment without metrics collection:

```bash
# Run audit script to identify affected workloads
./scripts/audit-exec-probes.sh

# Auto-remediate with default timeout (5s)
python scripts/auto-remediate-probes.py --timeout 5 --apply
```

## 📋 Best Practices

### Recommended Timeout Values

| Probe Type | Use Case | Recommended Timeout |
|------------|----------|-------------------|
| Simple health check | File existence, process check | 2-3 seconds |
| Database connectivity | Connection test | 5-10 seconds |
| Complex validation | Multi-step checks | 10-30 seconds |
| Application startup | Heavy initialization | 30-60 seconds |

### Timeout Calculation Formula

```
timeoutSeconds = ceiling(P99_execution_time * 1.2)
```

## 🔍 Metrics Exposed

| Metric | Type | Description |
|--------|------|-------------|
| `kubernetes_probe_duration_seconds` | Histogram | Probe execution duration |
| `kubernetes_probe_timeout_violations_total` | Counter | Probes exceeding 1s |
| `kubernetes_probe_observations_total` | Counter | Total probe executions |

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📚 References

- [Kubernetes Probe Documentation](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [GKE Release Notes](https://cloud.google.com/kubernetes-engine/docs/release-notes)
