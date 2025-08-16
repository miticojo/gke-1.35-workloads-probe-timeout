# Architecture Documentation

## Overview

The GKE 1.35 Probe Timeout Monitor uses a distributed architecture to collect, store, and analyze probe execution metrics without modifying existing workloads.

## Components

### 1. Metrics Collection Layer

**DaemonSet Exporter**
- Runs on every node in the cluster
- Monitors kubelet and container runtime logs
- Extracts probe execution timing information
- Exposes metrics in Prometheus format

### 2. Storage Layer

**Prometheus/Google Managed Prometheus**
- Time-series database for metrics
- Automatic aggregation and downsampling
- 15-day retention (configurable)

### 3. Analysis Layer

**Python Analysis Scripts**
- Query Prometheus for metrics
- Calculate P99 execution times
- Generate timeout recommendations

### 4. Visualization Layer

**Grafana/Cloud Monitoring**
- Real-time dashboards
- Alert configuration
- Historical trend analysis

## Data Flow

1. Probe Execution → Kubelet logs event
2. DaemonSet captures log → Metrics extracted
3. Prometheus scrapes metrics → Storage
4. Analysis script queries data → Recommendations
5. Patches applied to workloads

## Security Considerations

- DaemonSet requires privileged access for journal reading
- RBAC limits permissions to read-only for monitoring
- No external dependencies or data transmission

## Performance Impact

- CPU: 50m average per node
- Memory: 64Mi average per node
- Network: <1KB/s per node
- Storage: ~10KB/pod/day in Prometheus
