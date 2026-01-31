import subprocess


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
            ["helm", "repo", "add", "kubernetes-dashboard", "https://kubernetes.github.io/dashboard/"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print("✓ Successfully added Kubernetes Dashboard Helm repository")
            return True
        else:
            print("✗ Failed to add Kubernetes Dashboard Helm repository")
            print(result.stderr)
            return False
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
                "helm", "upgrade", "--install", "kubernetes-dashboard", "kubernetes-dashboard/kubernetes-dashboard",
                "--namespace", namespace,
                "--create-namespace",
                "--set", "kong.proxy.http.enabled=true",
                "--set", "kong.proxy.tls.enabled=false"
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
    
