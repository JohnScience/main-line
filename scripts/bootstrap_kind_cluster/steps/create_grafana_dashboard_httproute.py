import subprocess
import yaml
from pathlib import Path

from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind, Output
from scripts.kind_cluster.index import KIND_CLUSTER_NAME

project_root = Path(__file__).parent.parent.parent.parent


def create_grafana_dashboard_httproute(
    cluster_name: str = KIND_CLUSTER_NAME,
    namespace: str = "grafana-dashboard",
) -> tuple[bool, list[Output]]:
    """
    Creates the HTTPRoute for the Grafana Dashboard via Helm.

    Returns:
        tuple[bool, list[Output]]: Success status and list of outputs
    """
    print(f"\nCreating Grafana Dashboard HTTPRoute...")
    try:
        # Read the grafana port from gateway.yaml (look for 'grafana-direct' listener)
        gateway_yaml_path = project_root / "k8s" / "gateway.yaml"
        grafana_port = None
        try:
            with open(gateway_yaml_path, 'r') as f:
                gateway_config = yaml.safe_load(f)
                listeners = gateway_config.get('spec', {}).get('listeners', [])
                for listener in listeners:
                    if listener.get('name') == 'grafana-direct':
                        grafana_port = listener.get('port')
                        break
        except Exception as e:
            print(f"✗ Failed to read port from gateway.yaml: {e}")
            return False, []

        if grafana_port is None:
            print(f"✗ Failed to find 'grafana-direct' listener port in gateway.yaml")
            return False, []

        # Read gateway config and hostnames from the HTTPRoute chart values
        httproute_values_path = project_root / "k8s" / "grafana-dashboard" / "httproute" / "values.yaml"
        gateway_name = None
        gateway_namespace = None
        grafana_hostnames = []
        try:
            with open(httproute_values_path, 'r') as f:
                httproute_config = yaml.safe_load(f)
                gateway_name = httproute_config.get('gateway', {}).get('name')
                gateway_namespace = httproute_config.get('gateway', {}).get('namespace')
                grafana_hostnames = httproute_config.get('hostnames', {}).get('domain', [])
        except Exception as e:
            print(f"✗ Failed to read gateway configuration from httproute values.yaml: {e}")
            return False, []

        if not gateway_name or not gateway_namespace:
            print(f"✗ Failed to find gateway name or namespace in httproute values.yaml")
            return False, []

        if not grafana_hostnames:
            print(f"✗ Failed to find grafana hostnames in httproute values.yaml")
            return False, []

        primary_hostname = grafana_hostnames[0]

        # Get the Gateway LoadBalancer IP
        result = subprocess.run(
            ["kubectl", "get", "gateway", gateway_name, "-n", gateway_namespace,
             "-o", "jsonpath={.status.addresses[0].value}"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
        )
        gateway_ip = result.stdout.strip()

        if not gateway_ip:
            print("⚠ Warning: Gateway LoadBalancer IP not yet assigned, deploying without IP hostname")
            gateway_ip_arg = []
        else:
            gateway_ip_arg = ["--set", f"hostnames.gatewayIP={gateway_ip}"]

        # Deploy HTTPRoute via Helm
        httproute_chart_path = project_root / "k8s" / "grafana-dashboard" / "httproute"
        helm_command = [
            "helm", "upgrade", "--install",
            "grafana-dashboard-httproute", str(httproute_chart_path),
            "--namespace", namespace,
            "--create-namespace",
        ] + gateway_ip_arg

        subprocess.run(
            helm_command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        if gateway_ip:
            print(f"✓ Successfully created Grafana Dashboard HTTPRoute (accessible via {primary_hostname}, {gateway_ip}, and localhost:{grafana_port})")
            outputs = [
                Output(
                    title="Grafana Dashboard URL",
                    body=f"http://{primary_hostname} (Gateway IP: {gateway_ip}), http://localhost:{grafana_port}",
                )
            ]
        else:
            print(f"✓ Successfully created Grafana Dashboard HTTPRoute (accessible via {primary_hostname} and localhost:{grafana_port})")
            outputs = [
                Output(
                    title="Grafana Dashboard URL",
                    body=f"http://{primary_hostname}, http://localhost:{grafana_port}",
                )
            ]
        return True, outputs
    except Exception as e:
        print(f"✗ Failed to create Grafana Dashboard HTTPRoute: {e}")
        return False, []


CREATE_GRAFANA_DASHBOARD_HTTPROUTE = Step(
    name="create_grafana_dashboard_httproute",
    description="Creates the HTTPRoute for the Grafana Dashboard",
    perform=lambda **kwargs: create_grafana_dashboard_httproute(),
    rollback=None,
    step_kind=StepKind.Required(),
    perform_flag="create_grafana_dashboard_httproute_only",
    depends_on=['create_gateway', 'deploy_grafana_dashboard'],
)
