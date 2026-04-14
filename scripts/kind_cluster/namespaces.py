from enum import Enum, auto


class NamespaceEnum(str, Enum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        # kebab-case version of the enum member name
        return name.replace("_", "-").lower()

class DefaultNamespaces(NamespaceEnum):
    DEFAULT = auto()
    KUBE_SYSTEM = auto()
    KUBE_PUBLIC = auto()
    # https://stackoverflow.com/questions/59659966/what-is-the-kube-node-lease-namespace-for
    KUBE_NODE_LEASE = auto()


class KindNamespaces(NamespaceEnum):
    LOCAL_PATH_STORAGE = auto()


class UserDefinedNamespaces(NamespaceEnum):
    CERT_MANAGER = auto()
    ENVOY_GATEWAY_SYSTEM = auto()
    GRAFANA_ALLOY = auto()
    GRAFANA_DASHBOARD = auto()
    KUBERNETES_DASHBOARD = auto()
    LOKI = auto()
    METALLB_SYSTEM = auto()
    OPENTELEMETRY_COLLECTOR = auto()
    OPENTELEMETRY_OPERATOR = auto()
    PROMETHEUS = auto()


def merge_enums(name, *enums):
    members = {}
    for e in enums:
        members.update({k: v.value for k, v in e.__members__.items()})
    return NamespaceEnum(name, members)


Namespaces = merge_enums("Namespaces", DefaultNamespaces, KindNamespaces, UserDefinedNamespaces)
