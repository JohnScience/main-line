from scripts.bootstrap_kind_cluster.steps_base import Step, Output
from scripts.kind_cluster.index import KIND_CLUSTER_NAME
import scripts.common.kind as kind_module
import subprocess
import yaml
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent

def create_kubernetes_dashboard_httproute(cluster_name: str = KIND_CLUSTER_NAME) -> tuple[bool, list[Output]]:
    """
    Creates the HTTPRoute for the Kubernetes Dashboard via Helm.
    This allows dynamic configuration of hostnames including the Gateway IP.
    
    Args:
        cluster_name: Name of the Kind cluster
    Returns:
        tuple[bool, list[Output]]: Success status and list of outputs
    """
    print(f"\nCreating Kubernetes Dashboard HTTPRoute...")

    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name):
        print(f"✗ Failed to set kubectl context for Kind cluster '{cluster_name}'")
        return False, []
    
    try:
        # Read the dashboard port from gateway.yaml
        gateway_yaml_path = project_root / "k8s" / "gateway.yaml"
        dashboard_port = None
        try:
            with open(gateway_yaml_path, 'r') as f:
                gateway_config = yaml.safe_load(f)
                listeners = gateway_config.get('spec', {}).get('listeners', [])
                for listener in listeners:
                    if listener.get('name') == 'dashboard-direct':
                        dashboard_port = listener.get('port')
                        break
        except Exception as e:
            print(f"✗ Failed to read port from gateway.yaml: {e}")
            return False, []
        
        if dashboard_port is None:
            print(f"✗ Failed to find 'dashboard-direct' listener port in gateway.yaml")
            return False, []
        
        # Read the HTTPRoute chart path from values.yaml
        httproute_values_path = project_root / "k8s" / "kubernetes-dashboard" / "httproute" / "values.yaml"
        gateway_name = None
        gateway_namespace = None
        dashboard_hostnames = []
        try:
            with open(httproute_values_path, 'r') as f:
                httproute_config = yaml.safe_load(f)
                gateway_name = httproute_config.get('gateway', {}).get('name')
                gateway_namespace = httproute_config.get('gateway', {}).get('namespace')
                dashboard_hostnames = httproute_config.get('hostnames', {}).get('domain', [])
        except Exception as e:
            print(f"✗ Failed to read gateway configuration from httproute values.yaml: {e}")
            return False, []
        
        if not gateway_name or not gateway_namespace:
            print(f"✗ Failed to find gateway name or namespace in httproute values.yaml")
            return False, []
        
        if not dashboard_hostnames:
            print(f"✗ Failed to find dashboard hostnames in httproute values.yaml")
            return False, []
        
        # Use the first hostname as the primary dashboard URL
        primary_hostname = dashboard_hostnames[0]
        
        # Get the Gateway LoadBalancer IP
        result = subprocess.run(
            ["kubectl", "get", "gateway", gateway_name, "-n", gateway_namespace,
             "-o", "jsonpath={.status.addresses[0].value}"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        gateway_ip = result.stdout.strip()
        
        if not gateway_ip:
            print("⚠ Warning: Gateway LoadBalancer IP not yet assigned, deploying without IP hostname")
            gateway_ip_arg = []
        else:
            gateway_ip_arg = ["--set", f"hostnames.gatewayIP={gateway_ip}"]
        
        # Deploy HTTPRoute via Helm
        httproute_chart_path = project_root / "k8s" / "kubernetes-dashboard" / "httproute"
        
        helm_command = [
            "helm", "upgrade", "--install",
            "kubernetes-dashboard-httproute", str(httproute_chart_path),
            "--namespace", "kubernetes-dashboard",
            "--create-namespace"
        ] + gateway_ip_arg
        
        subprocess.run(
            helm_command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Deploy direct access HTTPRoute (for localhost:<port>)
        try:
            subprocess.run(
                ["kubectl", "apply", "-f", str(project_root / "k8s" / "kubernetes-dashboard" / "httproute-direct.yaml")],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception as e:
            print(f"⚠ Warning: Failed to create direct access HTTPRoute: {e}")
        
        if gateway_ip:
            print(f"✓ Successfully created Kubernetes Dashboard HTTPRoute (accessible via {primary_hostname}, {gateway_ip}, and localhost:{dashboard_port})")
            outputs = [
                Output(
                    title="Dashboard URL",
                    body=f"http://{primary_hostname} (Gateway IP: {gateway_ip}), http://localhost:{dashboard_port}"
                )
            ]
        else:
            print(f"✓ Successfully created Kubernetes Dashboard HTTPRoute (accessible via {primary_hostname} and localhost:{dashboard_port})")
            outputs = [
                Output(
                    title="Dashboard URL",
                    body=f"http://{primary_hostname}, http://localhost:{dashboard_port}"
                )
            ]
        return True, outputs
    except Exception as e:
        print(f"✗ Failed to create Kubernetes Dashboard HTTPRoute: {e}")
        return False, []

CREATE_KUBERNETES_DASHBOARD_HTTPROUTE = Step(
    name="create_kubernetes_dashboard_httproute",
    description="Creates the HTTPRoute for the Kubernetes Dashboard",
    perform=lambda **kwargs: create_kubernetes_dashboard_httproute(**kwargs),
    rollback=None,
    args={'cluster_name': KIND_CLUSTER_NAME},
    perform_flag="create_kubernetes_dashboard_httproute_only",
    step_kind=None,  # Set as needed
    depends_on=['create_gateway', 'create_kubernetes_dashboard_admin']
)
