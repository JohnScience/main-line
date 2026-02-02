# Project Transition and Observability Plan

## Intent

This project is transitioning from a docker-compose setup to a single-cluster, multi-node Kubernetes application. The main motivation is the single-tenancy requirement for chess engines, which makes docker-compose unfeasible for multi-user scenarios.

## Foundation First: Observability

Before migrating existing services, the initial focus is on building a solid observability foundation. This will ensure that metrics, logs, and traces are available for all services, making future troubleshooting and scaling easier.

## Service Migration

Once observability is in place, the plan is to move existing services into the Kubernetes cluster. Note that the chess-engine-broker service is yet to be built and will be included in future development phases.

## Observability Stack Introduction Plan

1. Prepare Helm charts or manifests for each component (recommended: use official Helm charts).
2. Deploy Prometheus for metrics collection.
	- Configure Prometheus to scrape metrics from your services and Kubernetes components.
3. Deploy OpenTelemetry Collector for traces and metrics.
	- Configure it to receive traces/metrics from your apps and export traces to Tempo, metrics to Prometheus.
4. Deploy Tempo for distributed tracing.
	- Connect OpenTelemetry Collector to Tempo.
5. Deploy Loki for log aggregation.
	- Configure your apps or cluster logging to send logs to Loki.
6. Deploy Grafana Dashboard.
	- Add Prometheus, Tempo, and Loki as data sources.
	- Import or create dashboards for metrics, traces, and logs.
7. Configure service discovery and authentication as needed.
8. Test the full observability pipeline: metrics, logs, and traces should appear in Grafana.

*Note: the document above is AI-generated and may require further refinement.*
