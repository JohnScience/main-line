# Project Transition and Observability Plan

## Intent

This project is transitioning from a docker-compose setup to a single-cluster, multi-node Kubernetes application. The main motivation is the single-tenancy requirement for chess engines, which makes docker-compose unfeasible for multi-user scenarios.

## Foundation First: Observability

Before migrating existing services, the initial focus is on building a solid observability foundation. This will ensure that metrics, logs, and traces are available for all services, making future troubleshooting and scaling easier.

## Service Migration

Once observability is in place, the plan is to move existing services into the Kubernetes cluster. Note that the chess-engine-broker service is yet to be built and will be included in future development phases.

## Observability Stack Introduction Plan

So far, the work has been done to introduce the Loki, Grafana Alloy for Grafana-specific OTLP collection, OpenTelemetry Operator, and OpenTelemetry Collector into the cluster.

Next steps include:

1. Add a dashboard in Grafana to visualize the collected logs.
2. Add Prometheus for metrics collection and create relevant dashboards.
3. Add Tempo for trace collection and create relevant dashboards.

*Note: the document above is AI-generated and may require further refinement.*


