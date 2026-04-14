import http.client
import json
import socket
import subprocess
import time
import urllib.parse
import uuid
from pathlib import Path

import yaml

from scripts.common.check_result import CheckFailed, CheckPassed, CheckResult
import scripts.common.kind as kind_module
from scripts.common.git import get_git_root
from scripts.kind_cluster.index import KIND_CLUSTER_NAME
from scripts.kind_cluster.namespaces import UserDefinedNamespaces, DefaultNamespaces, KindNamespaces, Namespaces
from scripts.kind_cluster.services import KnownServices

_PROJECT_ROOT = Path(get_git_root())

def _get_otel_collector_port(port_name: str) -> int:
    manifest = _PROJECT_ROOT / "k8s" / "opentelemetry-collector" / "OpenTelemetryCollector.yaml"
    doc = yaml.safe_load(manifest.read_text())
    for entry in doc["spec"]["ports"]:
        if entry["name"] == port_name:
            return int(entry["port"])
    raise KeyError(f"Port '{port_name}' not found in {manifest}")


_OTEL_COLLECTOR_HTTP_PORT = _get_otel_collector_port("otlp-http")

# Port 80 is the loki-gateway Helm chart default; it is not declared in k8s/loki/values.yaml.
_LOKI_GATEWAY_PORT = 80
_LOKI_TENANT_ID = "fake"

_TEST_SERVICE_NAME = "main-line-general-test"


def _port_forward(namespace: str, svc: KnownServices, local_port: int, remote_port: int) -> subprocess.Popen:
    # KnownServices values have the form "service/<name>"; kubectl wants just the name after "svc/".
    return subprocess.Popen(
        ["kubectl", "port-forward", svc.value, f"{local_port}:{remote_port}", "-n", namespace],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _wait_for_port(port: int, timeout: int = 10) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def _send_otlp_log(local_port: int, log_body: str) -> bool:
    payload = {
        "resourceLogs": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": _TEST_SERVICE_NAME}}
                    ]
                },
                "scopeLogs": [
                    {
                        "logRecords": [
                            {
                                "timeUnixNano": str(int(time.time() * 1e9)),
                                "severityText": "INFO",
                                "body": {"stringValue": log_body},
                            }
                        ]
                    }
                ],
            }
        ]
    }
    try:
        conn = http.client.HTTPConnection("127.0.0.1", local_port, timeout=10)
        conn.request(
            "POST",
            "/v1/logs",
            json.dumps(payload).encode(),
            {"Content-Type": "application/json"},
        )
        resp = conn.getresponse()
        resp.read()
        return resp.status in (200, 204)
    except Exception:
        return False


def _loki_contains_log(local_port: int, log_body: str, start_ns: int) -> bool:
    query = f'{{service_name="{_TEST_SERVICE_NAME}"}}'
    params = urllib.parse.urlencode({
        "query": query,
        "start": start_ns,
        "end": int(time.time() * 1e9) + int(5e9),
        "limit": 50,
    })
    try:
        conn = http.client.HTTPConnection("127.0.0.1", local_port, timeout=10)
        conn.request(
            "GET",
            f"/loki/api/v1/query_range?{params}",
            headers={"X-Scope-OrgID": _LOKI_TENANT_ID},
        )
        resp = conn.getresponse()
        body = resp.read()
        if resp.status != 200:
            return False
        data = json.loads(body)
        for stream in data.get("data", {}).get("result", []):
            for _ts, line in stream.get("values", []):
                if log_body in line:
                    return True
        return False
    except Exception:
        return False


def check_otlp_logs_received_by_loki(cluster_name: str = KIND_CLUSTER_NAME, **kwargs) -> CheckResult:
    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name, verbosity=0):
        return CheckFailed(errors=[f"Could not set kubectl context for cluster '{cluster_name}'"])

    log_body = f"otlp-loki-test-{uuid.uuid4()}"
    otel_local_port = 14318
    loki_local_port = 13100

    otel_pf = _port_forward(UserDefinedNamespaces.OPENTELEMETRY_COLLECTOR, KnownServices.OTEL_COLLECTOR_COLLECTOR, otel_local_port, _OTEL_COLLECTOR_HTTP_PORT)
    loki_pf = _port_forward(UserDefinedNamespaces.LOKI, KnownServices.LOKI_GATEWAY, loki_local_port, _LOKI_GATEWAY_PORT)
    try:
        if not _wait_for_port(otel_local_port):
            return CheckFailed(errors=["Timed out waiting for OTel Collector port-forward"])
        if not _wait_for_port(loki_local_port):
            return CheckFailed(errors=["Timed out waiting for Loki gateway port-forward"])

        start_ns = int(time.time() * 1e9)

        if not _send_otlp_log(otel_local_port, log_body):
            return CheckFailed(errors=["Failed to POST OTLP log to OTel Collector"])

        # The OTel Collector batch processor has a 10 s timeout; Alloy also batches.
        # Poll for up to 60 seconds.
        deadline = time.time() + 60
        while time.time() < deadline:
            if _loki_contains_log(loki_local_port, log_body, start_ns):
                return CheckPassed()
            time.sleep(3)

        return CheckFailed(errors=[
            f"OTLP log '{log_body}' was not found in Loki within 60 seconds"
        ])
    finally:
        otel_pf.terminate()
        loki_pf.terminate()


def check_all_namespaces_exist(cluster_name: str = KIND_CLUSTER_NAME, **kwargs) -> CheckResult:
    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name, verbosity=0):
        return CheckFailed(errors=[f"Could not set kubectl context for cluster '{cluster_name}'"])
    try:
        result = subprocess.run(
            ["kubectl", "get", "namespaces", "-o", "jsonpath={.items[*].metadata.name}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            return CheckFailed(errors=[f"kubectl get namespaces failed: {result.stderr.strip()}"])
    except FileNotFoundError:
        return CheckFailed(errors=["kubectl not found"])

    existing = set(result.stdout.split())
    known = {ns.value for ns in Namespaces}

    errors = []
    missing = [ns for ns in known if ns not in existing]
    if missing:
        errors.append(f"Namespaces in enum but not in cluster: {missing}")
    extra = [ns for ns in existing if ns not in known]
    if extra:
        errors.append(f"Namespaces in cluster but not in enum: {extra}")

    if errors:
        return CheckFailed(errors=errors)
    return CheckPassed()


def check_all_services_exist(cluster_name: str = KIND_CLUSTER_NAME, **kwargs) -> CheckResult:
    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name, verbosity=0):
        return CheckFailed(errors=[f"Could not set kubectl context for cluster '{cluster_name}'"])

    missing = []
    for svc in KnownServices:
        svc_name = svc.value.removeprefix("service/")
        namespace = svc.namespace()
        try:
            result = subprocess.run(
                ["kubectl", "get", "service", svc_name, "-n", namespace],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if result.returncode != 0:
                missing.append(f"{svc_name} (namespace: {namespace})")
        except FileNotFoundError:
            return CheckFailed(errors=["kubectl not found"])

    if missing:
        return CheckFailed(errors=[f"Services not found in cluster: {missing}"])
    return CheckPassed()
