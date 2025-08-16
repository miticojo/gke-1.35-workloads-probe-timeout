
# GKE 1.35 Workloads Probe Timeout Monitor

## Project Overview

This project provides a comprehensive solution for monitoring and remediating Kubernetes exec probe timeouts in preparation for GKE 1.35's ExecProbeTimeout enforcement. It includes a non-invasive monitoring solution that discovers all workloads using exec probes, monitors actual probe execution times without modifying workloads, analyzes metrics to recommend appropriate timeout values, and remediates by generating patches with optimal configurations.

The architecture consists of a DaemonSet exporter that sends metrics to Prometheus, which are then analyzed by Python scripts. The results are visualized in a Cloud Monitoring Dashboard.

## Building and Running

### Prerequisites
- Kubernetes cluster (GKE or any K8s >= 1.20)
- kubectl configured with cluster access
- Prometheus (or Google Managed Prometheus in GKE)
- Python 3.8+

### Key Commands

The project uses a `Makefile` to streamline common tasks:

- **`make install`**: Install Python dependencies from `requirements.txt`.
- **`make install-dev`**: Install development dependencies from `requirements-dev.txt`.
- **`make deploy`**: Deploy the monitoring stack to Kubernetes. This includes the probe metrics exporter DaemonSet.
- **`make analyze`**: Run the probe analysis script to generate recommendations.
- **`make audit`**: Run an audit script to identify affected workloads without metrics collection.
- **`make clean`**: Clean up generated files.
- **`make test`**: Run tests using pytest.
- **`make lint`**: Run linters (flake8 and mypy).
- **`make format`**: Format code using black.

### Running the Solution

1.  **Deploy the monitoring stack:**
    ```bash
    make deploy
    ```
2.  **Wait for metrics collection (24-48 hours).**
3.  **Analyze the metrics:**
    ```bash
    make analyze
    ```
4.  **Review and apply the generated patches.**

## Development Conventions

### Coding Style

- Python code is formatted with `black`.
- Python code is linted with `flake8` and type-checked with `mypy`.
- Shell scripts are checked with `shellcheck`.

### Testing

- Tests are written using `pytest`.
- The main focus of testing is on the analysis scripts.
- The CI pipeline runs tests for Python versions 3.8, 3.9, 3.10, and 3.11.

### CI/CD

- The project uses GitHub Actions for CI.
- The CI pipeline is defined in `.github/workflows/ci.yml`.
- The pipeline includes steps for installing dependencies, linting, testing, and validating YAML files.

### Contributing

- Contributions are welcome.
- Pull Requests should be submitted to the `main` branch.
