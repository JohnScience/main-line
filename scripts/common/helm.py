from pathlib import Path
import subprocess

from scripts.common import git


def is_helm_installed() -> bool:
    """
    Check if helm is installed and available in PATH.
    
    Returns:
        bool: True if helm is installed, False otherwise
    """
    try:
        result = subprocess.run(
            ["helm", "version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False

# https://groups.google.com/g/kubernetes-sig-ui/c/vpYIRDMysek/m/wd2iedUKDwAJ
def add_kubernetes_dashboard_helm_repo() -> bool:
    """
    Adds the Kubernetes Dashboard Helm repository.
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("\nAdding Kubernetes Dashboard Helm repository...")
    
    # Check if helm is installed
    if not is_helm_installed():
        print("✗ 'helm' is not installed or not in PATH")
        return False
    
    try:
        result = subprocess.run(
            ["helm", "repo", "add", "headlamp", "https://kubernetes-sigs.github.io/headlamp/"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print("✓ Successfully added Kubernetes Dashboard Helm repository")
        else:
            print("✗ Failed to add Kubernetes Dashboard Helm repository")
            print(result.stderr)
            return False

        result = subprocess.run(
            ["helm", "repo", "update", "headlamp"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        if result.returncode != 0:
            print("✗ Failed to update Kubernetes Dashboard Helm repository")
            print(result.stderr)
            return False

        print("✓ Successfully updated Kubernetes Dashboard Helm repository")
        return True
    except Exception as e:
        print(f"✗ Failed to add Helm repository: {e}")
        return False

def deploy_kubernetes_dashboard_via_helm(namespace: str = "kubernetes-dashboard") -> bool:
    """
    Deploys the Kubernetes Dashboard using Helm with HTTP enabled.
    
    This configures Kong proxy to serve HTTP instead of HTTPS, allowing
    the Gateway API to handle TLS termination.
    
    Args:
        namespace: Kubernetes namespace to deploy the dashboard into
    
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\nDeploying Kubernetes Dashboard in namespace '{namespace}' via Helm...")
    
    if not add_kubernetes_dashboard_helm_repo():
        return False
    
    try:
        result = subprocess.run(
            [
                "helm", "upgrade", "--install", "headlamp-kubernetes-dashboard", "headlamp/headlamp",
                "--namespace", namespace,
                "--create-namespace"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print("✓ Successfully deployed Kubernetes Dashboard via Helm")
            return True
        else:
            print("✗ Failed to deploy Kubernetes Dashboard via Helm")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"✗ Failed to deploy Kubernetes Dashboard: {e}")
        return False

def deploy_envoy_gateway_via_helm(namespace: str = "envoy-gateway-system") -> bool:
    """
    Deploys the Envoy Gateway using Helm.
    
    Args:
        namespace: Kubernetes namespace to deploy the Envoy Gateway into
    
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\nDeploying Envoy Gateway in namespace '{namespace}' via Helm...")
    
    # Check if helm is installed
    if not is_helm_installed():
        print("✗ 'helm' is not installed or not in PATH")
        return False
    
    try:
        result = subprocess.run(
            [
                "helm", "upgrade", "--install", "eg", "oci://docker.io/envoyproxy/gateway-helm",
                "--version", "v1.6.2",
                "--namespace", namespace,
                "--create-namespace",
                "--skip-crds"  # Skip CRD installation since Gateway API CRDs can be installed separately
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print("✓ Successfully deployed Envoy Gateway via Helm")
            return True
        else:
            print("✗ Failed to deploy Envoy Gateway via Helm")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"✗ Failed to deploy Envoy Gateway: {e}")
        return False
    
def add_grafana_helm_repo() -> bool:
    """
    Adds the Grafana Helm repository.
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("\nAdding Grafana Helm repository...")
    
    # Check if helm is installed
    if not is_helm_installed():
        print("✗ 'helm' is not installed or not in PATH")
        return False
    
    try:
        result = subprocess.run(
            ["helm", "repo", "add", "grafana", "https://grafana.github.io/helm-charts"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print("✓ Successfully added Grafana Helm repository")
        else:
            print("✗ Failed to add Grafana Helm repository")
            print(result.stderr)
            return False

        result = subprocess.run(
            ["helm", "repo", "update", "grafana"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        if result.returncode != 0:
            print("✗ Failed to update Grafana Helm repository")
            print(result.stderr)
            return False

        print("✓ Successfully updated Grafana Helm repository")
        return True
    except Exception as e:
        print(f"✗ Failed to add Helm repository: {e}")
        return False

def deploy_loki_via_helm(namespace: str = "loki") -> bool:
    """
    Deploys Loki for log aggregation using Helm.
    
    Args:
        namespace: Kubernetes namespace to deploy Loki into
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\nDeploying Loki in namespace '{namespace}' via Helm...")

    git_root = git.get_git_root()

    if not git_root:
        print("✗ Could not determine Git root directory.")
        return False
    
    values_file_path = Path(git_root) / "k8s" / "loki" / "values.yaml"
    
    try:
        result = subprocess.run(
            [
                "helm", "upgrade", "--install", "loki", "grafana/loki",
                "--values", str(values_file_path),
                "--namespace", namespace,
                "--create-namespace",
                
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print("✓ Successfully deployed Loki via Helm")
            return True
        else:
            print("✗ Failed to deploy Loki via Helm")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"✗ Failed to deploy Loki: {e}")
        return False

def add_opentelemetry_helm_repo() -> bool:
    """
    Adds the OpenTelemetry Helm repository.
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("\nAdding OpenTelemetry Helm repository...")
    
    # Check if helm is installed
    if not is_helm_installed():
        print("✗ 'helm' is not installed or not in PATH")
        return False
    
    try:
        result = subprocess.run(
            ["helm", "repo", "add", "open-telemetry", "https://open-telemetry.github.io/opentelemetry-helm-charts"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print("✓ Successfully added OpenTelemetry Helm repository")
        else:
            print("✗ Failed to add OpenTelemetry Helm repository")
            print(result.stderr)
            return False

        result = subprocess.run(
            ["helm", "repo", "update", "open-telemetry"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        if result.returncode != 0:
            print("✗ Failed to update OpenTelemetry Helm repository")
            print(result.stderr)
            return False

        print("✓ Successfully updated OpenTelemetry Helm repository")
        return True
    except Exception as e:
        print(f"✗ Failed to add Helm repository: {e}")
        return False

def add_prometheus_community_helm_repo() -> bool:
    """
    Adds the Prometheus Community Helm repository.
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("\nAdding Prometheus Community Helm repository...")
    
    # Check if helm is installed
    if not is_helm_installed():
        print("✗ 'helm' is not installed or not in PATH")
        return False
    
    try:
        result = subprocess.run(
            ["helm", "repo", "add", "prometheus-community", "https://prometheus-community.github.io/helm-charts"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print("✓ Successfully added Prometheus Community Helm repository")
        else:
            print("✗ Failed to add Prometheus Community Helm repository")
            print(result.stderr)
            return False

        result = subprocess.run(
            ["helm", "repo", "update", "prometheus-community"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        if result.returncode != 0:
            print("✗ Failed to update Prometheus Community Helm repository")
            print(result.stderr)
            return False

        print("✓ Successfully updated Prometheus Community Helm repository")
        return True
    except Exception as e:
        print(f"✗ Failed to add Helm repository: {e}")
        return False

def deploy_prometheus_via_helm(namespace: str = "prometheus") -> bool:
    """
    Deploys Prometheus using the prometheus-community Helm chart.

    Args:
        namespace: Kubernetes namespace to deploy Prometheus into
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\nDeploying Prometheus in namespace '{namespace}' via Helm...")

    if not is_helm_installed():
        print("✗ 'helm' is not installed or not in PATH")
        return False

    git_root = git.get_git_root()
    values_file_path = Path(git_root) / "k8s" / "prometheus" / "values.yaml"

    try:
        result = subprocess.run(
            [
                "helm", "upgrade", "--install", "prometheus", "prometheus-community/prometheus",
                "--namespace", namespace,
                "--create-namespace",
                "--values", str(values_file_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )

        if result.returncode == 0:
            print("✓ Successfully deployed Prometheus via Helm")
            return True
        else:
            print("✗ Failed to deploy Prometheus via Helm")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"✗ Failed to deploy Prometheus: {e}")
        return False

def deploy_cert_manager_via_helm(namespace: str = "cert-manager") -> bool:
    """
    Deploys Cert-Manager using Helm.
    
    Args:
        namespace: Kubernetes namespace to deploy Cert-Manager into
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\nDeploying Cert-Manager in namespace '{namespace}' via Helm...")
    
    # Check if helm is installed
    if not is_helm_installed():
        print("✗ 'helm' is not installed or not in PATH")
        return False
    
    try:
        result = subprocess.run(
            [
                "helm", "upgrade", "--install", "cert-manager", "oci://quay.io/jetstack/charts/cert-manager",
                "--version", "v1.19.2",
                "--namespace", namespace,
                "--create-namespace",
                "--set", "crds.enabled=true"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print("✓ Successfully deployed Cert-Manager via Helm")
            return True
        else:
            print("✗ Failed to deploy Cert-Manager via Helm")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"✗ Failed to deploy Cert-Manager: {e}")
        return False

def deploy_opentelemetry_operator_via_helm(namespace: str = "opentelemetry-operator") -> bool:
    """
    Deploys OpenTelemetry Operator using Helm.

    Args:
        namespace: Kubernetes namespace to deploy OpenTelemetry Operator into
    Returns:
        bool: True if successful, False otherwise
    """

    print(f"\nDeploying OpenTelemetry Operator in namespace '{namespace}' via Helm...")
    
    try:
        result = subprocess.run(
            [
                "helm", "upgrade", "--install", "opentelemetry-operator", "open-telemetry/opentelemetry-operator",
                "--namespace", namespace,
                "--create-namespace"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print("✓ Successfully deployed OpenTelemetry Operator via Helm")
            return True
        else:
            print("✗ Failed to deploy OpenTelemetry Operator via Helm")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"✗ Failed to deploy OpenTelemetry Operator: {e}")
        return False

def deploy_alloy_via_helm(namespace: str = "grafana-alloy") -> bool:
    """
    Deploys Grafana Alloy using Helm.

    Args:
        namespace: Kubernetes namespace to deploy Grafana Alloy into
    Returns:
        bool: True if successful, False otherwise
    """

    print(f"\nDeploying Grafana Alloy in namespace '{namespace}' via Helm...")
    
    git_root = git.get_git_root()

    try:
        result = subprocess.run(
            [
                "helm", "upgrade", "--install", "grafana", "grafana/alloy",
                "--namespace", namespace,
                "-f", Path(git_root) / "k8s" / "grafana-alloy" / "values.yaml"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print("✓ Successfully deployed Grafana Alloy via Helm")
            return True
        else:
            print("✗ Failed to deploy Grafana Alloy via Helm")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"✗ Failed to deploy Grafana Alloy: {e}")
        return False

def deploy_grafana_dashboard_via_helm(
    namespace: str,
    logical_chart_name: str = "main-line-grafana-dashboard",
    root_url: str | None = None,
) -> bool:
    """
    Deploys a Grafana dashboard using the Grafana Helm chart and a custom values.yaml manifest.

    Args:
        namespace: The Kubernetes namespace to deploy the dashboard into.
        logical_chart_name: The Helm release name for the dashboard deployment (default: 'main-line-grafana-dashboard').
        root_url: Optional Grafana root_url (GF_SERVER_ROOT_URL). Should match the external URL used to access Grafana.

    Returns:
        bool: True if deployment was successful, False otherwise.
    """

    git_root = git.get_git_root()

    if not git_root:
        print("✗ Could not determine Git root directory.")
        return False

    manifest = Path(git_root) / "k8s" / "grafana-dashboard" / "values.yaml"

    # helm upgrade --install <logical-chart-name> grafana/grafana --namespace <namespace> -f <manifest>

    cmd = [
        "helm", "upgrade", "--install", logical_chart_name, "grafana/grafana",
        "--namespace", namespace,
        "-f", str(manifest),
    ]
    if root_url:
        cmd += ["--set", f"grafana\\.ini.server.root_url={root_url}"]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print(f"✓ Successfully deployed Grafana Dashboard via Helm in namespace '{namespace}'")
            return True
        else:
            print(f"✗ Failed to deploy Grafana Dashboard via Helm in namespace '{namespace}'")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"✗ Failed to deploy Grafana Dashboard: {e}")
        return False
