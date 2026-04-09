from scripts.bootstrap_kind_cluster.steps_base import Step, Output
from scripts.bootstrap_kind_cluster.check_result import CheckPassed, CheckFailed, CheckResult
from scripts.kind_cluster.index import KIND_CLUSTER_NAME
import scripts.common.kind as kind_module
import subprocess
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent

def create_kubernetes_dashboard_admin(cluster_name: str = KIND_CLUSTER_NAME) -> tuple[bool, list[Output]]:
    """
    Creates the service account and cluster role binding for the Kubernetes Dashboard admin user.
    
    Args:
        cluster_name: Name of the Kind cluster
    
    Returns:
        tuple[bool, list[Output]]: Success status and list of outputs
    """
    print(f"\nCreating Kubernetes Dashboard admin user...")

    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name):
        print(f"✗ Failed to set kubectl context for Kind cluster '{cluster_name}'")
        return False, []
    
    try:
        subprocess.run(
            ["kubectl", "apply", "-f", str(project_root / "k8s" / "kubernetes-dashboard" / "kubernetes-dashboard-admin.yaml")],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(f"✓ Successfully created Kubernetes Dashboard admin user service account")
    except Exception as e:
        print(f"✗ Failed to create Kubernetes Dashboard admin user service account: {e}")
        return False, []
    
    try:
        subprocess.run(
            ["kubectl", "apply", "-f", str(project_root / "k8s" / "base" / "cluster-admin-role-binding.yaml")],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(f"✓ Successfully created ClusterRoleBinding for admin user")
    except Exception as e:
        print(f"✗ Failed to create ClusterRoleBinding for admin user: {e}")
        return False, []

    # Try to get the dashboard admin token
    try:
        result = subprocess.run(
            [
                "kubectl", "create", "token", "kubernetes-dashboard-admin", "-n", "kubernetes-dashboard"
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        token = result.stdout.strip()
        outputs = [Output(title="Kubernetes Dashboard Admin Token (`kubectl create token kubernetes-dashboard-admin -n kubernetes-dashboard`)", body=token)] if token else []
        if token:
            print(f"✓ Retrieved Kubernetes Dashboard admin token")
        else:
            print(f"⚠ No token returned by kubectl create token")
        return True, outputs
    except Exception as e:
        print(f"✗ Failed to get Kubernetes Dashboard admin token: {e}")
        return True, []
    except Exception as e:
        print(f"✗ Failed to create ClusterRoleBinding for admin user: {e}")
        return False

def check_kubernetes_dashboard_admin_created(cluster_name: str = KIND_CLUSTER_NAME, **kwargs) -> CheckResult:
    """Check that the kubernetes-dashboard-admin ServiceAccount exists."""
    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name, verbosity=0):
        return CheckFailed(errors=[f"Could not set kubectl context for cluster '{cluster_name}'"])
    try:
        result = subprocess.run(
            ["kubectl", "get", "serviceaccount", "kubernetes-dashboard-admin",
             "--namespace", "kubernetes-dashboard"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            return CheckPassed()
        return CheckFailed(errors=["ServiceAccount 'kubernetes-dashboard-admin' not found in namespace 'kubernetes-dashboard'"])
    except FileNotFoundError:
        return CheckFailed(errors=["kubectl not found"])


CREATE_KUBERNETES_DASHBOARD_ADMIN = Step(
    name="create_kubernetes_dashboard_admin",
    description="Creates the service account and cluster role binding for the Kubernetes Dashboard admin user",
    perform=lambda **kwargs: create_kubernetes_dashboard_admin(**kwargs),
    check=lambda **kwargs: check_kubernetes_dashboard_admin_created(**kwargs),
    rollback=None,
    args={'cluster_name': KIND_CLUSTER_NAME},
    perform_flag='create_dashboard_admin_only',
    step_kind=None,  # Set as needed
    depends_on=['deploy_kubernetes_dashboard']
)
