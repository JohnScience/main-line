from enum import Enum, auto

from scripts.kind_cluster.namespaces import UserDefinedNamespaces, DefaultNamespaces, KindNamespaces


class ServiceEnum(str, Enum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        # kebab-case version of the enum member name
        return "service/" + name.replace("_", "-").lower()


class KnownServices(ServiceEnum):
    CERT_MANAGER = auto()
    CERT_MANAGER_CAINJECTOR = auto()
    CERT_MANAGER_WEBHOOK = auto()
    KUBERNETES = auto()
    # ENVOY_DEFAULT_MAIN_LINE_GATEWAY_HASH = "service/envoy-default-main-line-gateway-{hash}"
    ENVOY_GATEWAY = auto()
    GRAFANA_ALLOY = auto()
    MAIN_LINE_GRAFANA_DASHBOARD = auto()
    KUBE_DNS = auto()
    HEADLAMP_KUBERNETES_DASHBOARD = auto()
    LOKI_BACKEND = auto()
    LOKI_BACKEND_HEADLESS = auto()
    LOKI_CANARY = auto()
    LOKI_CHUNKS_CACHE = auto()
    LOKI_GATEWAY = auto()
    LOKI_MEMBERLIST = auto()
    LOKI_MINIO = auto()
    LOKI_MINIO_CONSOLE = auto()
    LOKI_MINIO_SVC = auto()
    LOKI_QUERY_SCHEDULER_DISCOVERY = auto()
    LOKI_READ = auto()
    LOKI_READ_HEADLESS = auto()
    LOKI_RESULTS_CACHE = auto()
    LOKI_WRITE = auto()
    LOKI_WRITE_HEADLESS = auto()
    METALLB_WEBHOOK_SERVICE = auto()
    OTEL_COLLECTOR_COLLECTOR = auto()
    OTEL_COLLECTOR_COLLECTOR_HEADLESS = auto()
    OTEL_COLLECTOR_COLLECTOR_MONITORING = auto()
    OPENTELEMETRY_OPERATOR = auto()
    OPENTELEMETRY_OPERATOR_WEBHOOK = auto()
    PROMETHEUS_ALERTMANAGER = auto()
    PROMETHEUS_ALERTMANAGER_HEADLESS = auto()
    PROMETHEUS_KUBE_STATE_METRICS = auto()
    PROMETHEUS_PROMETHEUS_NODE_EXPORTER = auto()
    PROMETHEUS_PROMETHEUS_PUSHGATEWAY = auto()
    PROMETHEUS_SERVER = auto()

    def namespace(self) -> str:
        return _SERVICE_NAMESPACES[self.value]


_SERVICE_NAMESPACES: dict[KnownServices, UserDefinedNamespaces] = {
    KnownServices.CERT_MANAGER: UserDefinedNamespaces.CERT_MANAGER,
    KnownServices.CERT_MANAGER_CAINJECTOR: UserDefinedNamespaces.CERT_MANAGER,
    KnownServices.CERT_MANAGER_WEBHOOK: UserDefinedNamespaces.CERT_MANAGER,
    KnownServices.KUBERNETES: DefaultNamespaces.DEFAULT,
    # KnownServices.ENVOY_DEFAULT_MAIN_LINE_GATEWAY_HASH: UserDefinedNamespaces.ENVOY_GATEWAY_SYSTEM,
    KnownServices.ENVOY_GATEWAY: UserDefinedNamespaces.ENVOY_GATEWAY_SYSTEM,
    KnownServices.GRAFANA_ALLOY: UserDefinedNamespaces.GRAFANA_ALLOY,
    KnownServices.MAIN_LINE_GRAFANA_DASHBOARD: UserDefinedNamespaces.GRAFANA_DASHBOARD,
    KnownServices.KUBE_DNS: DefaultNamespaces.KUBE_SYSTEM,
    KnownServices.HEADLAMP_KUBERNETES_DASHBOARD: UserDefinedNamespaces.KUBERNETES_DASHBOARD,
    KnownServices.LOKI_BACKEND: UserDefinedNamespaces.LOKI,
    KnownServices.LOKI_BACKEND_HEADLESS: UserDefinedNamespaces.LOKI,
    KnownServices.LOKI_CANARY: UserDefinedNamespaces.LOKI,
    KnownServices.LOKI_CHUNKS_CACHE: UserDefinedNamespaces.LOKI,
    KnownServices.LOKI_GATEWAY: UserDefinedNamespaces.LOKI,
    KnownServices.LOKI_MEMBERLIST: UserDefinedNamespaces.LOKI,
    KnownServices.LOKI_MINIO: UserDefinedNamespaces.LOKI,
    KnownServices.LOKI_MINIO_CONSOLE: UserDefinedNamespaces.LOKI,
    KnownServices.LOKI_MINIO_SVC: UserDefinedNamespaces.LOKI,
    KnownServices.LOKI_QUERY_SCHEDULER_DISCOVERY: UserDefinedNamespaces.LOKI,
    KnownServices.LOKI_READ: UserDefinedNamespaces.LOKI,
    KnownServices.LOKI_READ_HEADLESS: UserDefinedNamespaces.LOKI,
    KnownServices.LOKI_RESULTS_CACHE: UserDefinedNamespaces.LOKI,
    KnownServices.LOKI_WRITE: UserDefinedNamespaces.LOKI,
    KnownServices.LOKI_WRITE_HEADLESS: UserDefinedNamespaces.LOKI,
    KnownServices.METALLB_WEBHOOK_SERVICE: UserDefinedNamespaces.METALLB_SYSTEM,
    KnownServices.OTEL_COLLECTOR_COLLECTOR: UserDefinedNamespaces.OPENTELEMETRY_COLLECTOR,
    KnownServices.OTEL_COLLECTOR_COLLECTOR_HEADLESS: UserDefinedNamespaces.OPENTELEMETRY_COLLECTOR,
    KnownServices.OTEL_COLLECTOR_COLLECTOR_MONITORING: UserDefinedNamespaces.OPENTELEMETRY_COLLECTOR,
    KnownServices.OPENTELEMETRY_OPERATOR: UserDefinedNamespaces.OPENTELEMETRY_OPERATOR,
    KnownServices.OPENTELEMETRY_OPERATOR_WEBHOOK: UserDefinedNamespaces.OPENTELEMETRY_OPERATOR,
    KnownServices.PROMETHEUS_ALERTMANAGER: UserDefinedNamespaces.PROMETHEUS,
    KnownServices.PROMETHEUS_ALERTMANAGER_HEADLESS: UserDefinedNamespaces.PROMETHEUS,
    KnownServices.PROMETHEUS_KUBE_STATE_METRICS: UserDefinedNamespaces.PROMETHEUS,
    KnownServices.PROMETHEUS_PROMETHEUS_NODE_EXPORTER: UserDefinedNamespaces.PROMETHEUS,
    KnownServices.PROMETHEUS_PROMETHEUS_PUSHGATEWAY: UserDefinedNamespaces.PROMETHEUS,
    KnownServices.PROMETHEUS_SERVER: UserDefinedNamespaces.PROMETHEUS,
}

_missing = [s for s in KnownServices if s not in _SERVICE_NAMESPACES]
assert not _missing, f"_SERVICE_NAMESPACES is missing entries for: {_missing}"
