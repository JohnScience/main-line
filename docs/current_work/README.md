# Project Transition and Observability Plan

## Intent

This project is transitioning from a docker-compose setup to a single-cluster, multi-node Kubernetes application. The main motivation is the single-tenancy requirement for chess engines, which makes docker-compose unfeasible for multi-user scenarios.

## Foundation First: Observability

Before migrating existing services, the initial focus is on building a solid observability foundation. This will ensure that metrics, logs, and traces are available for all services, making future troubleshooting and scaling easier.

## Service Migration

Once observability is in place, the plan is to move existing services into the Kubernetes cluster. Note that the chess-engine-broker service is yet to be built and will be included in future development phases.

## Observability Stack Introduction Plan

### Step-by-step Plan

1. Deploy the OpenTelemetry Collector (OTEL) in the cluster as the first observability component.
	- Verify that the OTEL collector is running and can receive telemetry data.

2. Introduce services one-by-one into the cluster.
	- After each service is deployed, configure it to send telemetry (metrics, logs, traces) to the OTEL collector.
	- At each step, verify that the OTEL collector is receiving and processing data from the new service.
	- Ensure that you can view the produced telemetry in the appropriate backend (Prometheus, Tempo, Loki) and in Grafana.

3. Deploy Prometheus for metrics collection.
	- Configure Prometheus to scrape metrics from OTEL collector and services.

4. Deploy Tempo for distributed tracing.
	- Connect OTEL collector to Tempo for trace export.

5. Deploy Loki for log aggregation.
	- Configure OTEL collector and services to send logs to Loki.

6. Deploy Grafana Dashboard.
	- Add Prometheus, Tempo, and Loki as data sources.
	- Import or create dashboards for metrics, traces, and logs.

7. Configure service discovery and authentication as needed.

8. Continuously test and verify the observability pipeline after each new service is added, ensuring all telemetry is visible in Grafana.

*Note: the document above is AI-generated and may require further refinement.*
