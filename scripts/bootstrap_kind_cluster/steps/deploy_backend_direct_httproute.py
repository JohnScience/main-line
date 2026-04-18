import subprocess
from pathlib import Path

from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind
from scripts.common.check_result import CheckPassed, CheckFailed, CheckResult
import scripts.common.kind as kind_module
from scripts.kind_cluster.index import KIND_CLUSTER_NAME

project_root = Path(__file__).parent.parent.parent.parent


def deploy_backend_direct_httproute(cluster_name: str = KIND_CLUSTER_NAME) -> bool:
    """
    Deploys the direct HTTPRoute for the backend from
    k8s/backend/httproute-direct.yaml.

    This binds the backend to the 'backend-direct' Gateway listener (port 8004),
    allowing direct access from outside the cluster without DNS configuration.

    Args:
        cluster_name: Name of the Kind cluster
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\nDeploying backend direct HTTPRoute...")

    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name):
        print(f"✗ Failed to set kubectl context for Kind cluster '{cluster_name}'")
        return False

    try:
        subprocess.run(
            ["kubectl", "apply", "-f", str(project_root / "k8s" / "backend" / "httproute-direct.yaml")],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print("✓ Successfully deployed backend-direct HTTPRoute")
        return True
    except Exception as e:
        print(f"✗ Failed to deploy backend-direct HTTPRoute: {e}")
        return False


def check_backend_direct_httproute(cluster_name: str = KIND_CLUSTER_NAME, **kwargs) -> CheckResult:
    """Check that the backend-direct HTTPRoute exists in the backend namespace."""
    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name, verbosity=0):
        return CheckFailed(errors=[f"Could not set kubectl context for cluster '{cluster_name}'"])
    try:
        result = subprocess.run(
            ["kubectl", "get", "httproute", "backend-direct", "--namespace", "backend"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            return CheckPassed()
        return CheckFailed(errors=["HTTPRoute 'backend-direct' not found in namespace 'backend'"])
    except FileNotFoundError:
        return CheckFailed(errors=["kubectl not found"])


DEPLOY_BACKEND_DIRECT_HTTPROUTE = Step(
    name="deploy_backend_direct_httproute",
    description="Deploys the direct HTTPRoute for the backend (port 8004), enabling access without DNS configuration",
    perform=lambda **kwargs: deploy_backend_direct_httproute(**kwargs),
    check=lambda **kwargs: check_backend_direct_httproute(**kwargs),
    rollback=None,
    args={'cluster_name': KIND_CLUSTER_NAME},
    perform_flag="deploy_backend_direct_httproute_only",
    step_kind=StepKind.Required(),
    depends_on=['create_gateway', 'deploy_backend'],
)
