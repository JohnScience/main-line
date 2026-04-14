#!/usr/bin/env python3
"""
Obtain credentials from the running Kind cluster.

Retrieves:
  - Kubernetes Dashboard admin token
  - Grafana admin password
"""

import base64
import subprocess
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import scripts.common.kind as kind_module
from scripts.kind_cluster.index import KIND_CLUSTER_NAME


def get_kubernetes_dashboard_token(cluster_name: str = KIND_CLUSTER_NAME) -> str | None:
    try:
        result = subprocess.run(
            [
                "kubectl", "create", "token",
                "kubernetes-dashboard-admin",
                "-n", "kubernetes-dashboard",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        return result.stdout.strip() or None
    except subprocess.CalledProcessError as e:
        stderr = e.stderr if isinstance(e.stderr, str) else e.stderr.decode()
        print(f"✗ Failed to get Kubernetes Dashboard admin token: {stderr}")
        return None
    except FileNotFoundError:
        print("✗ kubectl not found")
        return None


def _get_grafana_secret_field(namespace: str, secret_name: str, field: str) -> str | None:
    try:
        result = subprocess.run(
            [
                "kubectl", "get", "secret",
                "--namespace", namespace,
                secret_name,
                "-o", f"jsonpath={{.data.{field}}}",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        value_b64 = result.stdout.strip()
        if not value_b64:
            print(f"✗ Grafana secret field '{field}' not found in secret '{secret_name}'")
            return None
        return base64.b64decode(value_b64).decode("utf-8")
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode() if hasattr(e.stderr, "decode") else str(e.stderr)
        print(f"✗ Failed to retrieve Grafana secret field '{field}': {stderr}")
        return None
    except FileNotFoundError:
        print("✗ kubectl not found")
        return None


def get_grafana_credentials(namespace: str = "grafana-dashboard") -> tuple[str | None, str | None]:
    """Returns (admin_user, admin_password)."""
    secret_name = "main-line-grafana-dashboard"
    admin_user = _get_grafana_secret_field(namespace, secret_name, "admin-user")
    admin_password = _get_grafana_secret_field(namespace, secret_name, "admin-password")
    return admin_user, admin_password


def main() -> int:
    if not kind_module.set_kubectl_context_for_kind_cluster(KIND_CLUSTER_NAME):
        print(f"✗ Failed to set kubectl context for Kind cluster '{KIND_CLUSTER_NAME}'")
        return 1

    credentials: list[tuple[str, str]] = []

    token = get_kubernetes_dashboard_token()
    if token:
        credentials.append(("Kubernetes Dashboard Admin Token", token))
    else:
        print("⚠ Could not retrieve Kubernetes Dashboard admin token")

    grafana_user, grafana_password = get_grafana_credentials()
    if grafana_user or grafana_password:
        credentials.append(("Grafana Admin Username", grafana_user or "(not found)"))
        credentials.append(("Grafana Admin Password", grafana_password or "(not found)"))
    else:
        print("⚠ Could not retrieve Grafana credentials")

    if credentials:
        print("\n" + "=" * 60)
        print("Cluster Credentials:")
        print("=" * 60)
        for title, value in credentials:
            print(f"\n{title}:")
            print(f"  {value}")
        print("\n" + "=" * 60)

    return 0 if credentials else 1


if __name__ == "__main__":
    sys.exit(main())
