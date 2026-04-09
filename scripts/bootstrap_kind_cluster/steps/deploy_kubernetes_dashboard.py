import subprocess
from scripts.bootstrap_kind_cluster.steps_base import Step
from scripts.bootstrap_kind_cluster.check_result import CheckPassed, CheckFailed, CheckResult
from scripts.kind_cluster.index import KIND_CLUSTER_NAME
import scripts.common.kind as kind_module
import scripts.common.helm as helm_module

def deploy_kubernetes_dashboard(cluster_name: str = KIND_CLUSTER_NAME) -> bool:
    """
    Deploy the Kubernetes Dashboard in the specified Kind cluster.
    
    Args:
        cluster_name: Name of the Kind cluster
    
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\nDeploying Kubernetes Dashboard in Kind cluster '{cluster_name}'...")
    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name):
        print(f"✗ Failed to set kubectl context for Kind cluster '{cluster_name}'")
        return False
    
    if not helm_module.deploy_kubernetes_dashboard_via_helm():
        print(f"✗ Failed to deploy Kubernetes Dashboard via Helm in Kind cluster '{cluster_name}'")
        return False
    
    print(f"✓ Successfully deployed Kubernetes Dashboard in Kind cluster '{cluster_name}'")
    return True

def check_kubernetes_dashboard_deployed(cluster_name: str = KIND_CLUSTER_NAME, **kwargs) -> CheckResult:
    """Check that the Kubernetes Dashboard deployment exists in the cluster."""
    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name, verbosity=0):
        return CheckFailed(errors=[f"Could not set kubectl context for cluster '{cluster_name}'"])
    try:
        result = subprocess.run(
            ["kubectl", "get", "deployment", "headlamp-kubernetes-dashboard",
             "--namespace", "kubernetes-dashboard"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            return CheckPassed()
        return CheckFailed(errors=["Kubernetes Dashboard deployment not found in namespace 'kubernetes-dashboard'"])
    except FileNotFoundError:
        return CheckFailed(errors=["kubectl not found"])


DEPLOY_KUBERNETES_DASHBOARD = Step(
    name="deploy_kubernetes_dashboard",
    description="Deploys the Kubernetes Dashboard in the Kind cluster",
    perform=lambda **kwargs: deploy_kubernetes_dashboard(**kwargs),
    check=lambda **kwargs: check_kubernetes_dashboard_deployed(**kwargs),
    rollback=None,
    args={'cluster_name': KIND_CLUSTER_NAME},
    perform_flag='deploy_dashboard_only',
    step_kind=None,  # Set as needed
    depends_on=['initialize_kind_cluster']
)
