from scripts.bootstrap_kind_cluster.steps_base import Step
from scripts.common.check_result import CheckPassed, CheckFailed, CheckResult
from scripts.kind_cluster.index import KIND_CLUSTER_NAME
import scripts.common.kind as kind_module
import subprocess
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent

def create_gatewayclass_in_kind_cluster(
        cluster_name: str = KIND_CLUSTER_NAME,
) -> bool:
    """
    Create a GatewayClass resource in the Kind cluster.
    
    Args:
        cluster_name: Name of the Kind cluster
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\nCreating GatewayClass in Kind cluster '{cluster_name}'...")
    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name):
        print(f"✗ Failed to set kubectl context for Kind cluster '{cluster_name}'")
        return False
    try:
        subprocess.run(
            ["kubectl", "apply", "-f", str(project_root / "k8s" / "gatewayclass.yaml")],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(f"✓ Successfully created GatewayClass")
        return True
    except Exception as e:
        print(f"✗ Failed to create GatewayClass: {e}")
        return False


def check_gatewayclass_created(cluster_name: str = KIND_CLUSTER_NAME, **kwargs) -> CheckResult:
    """Check that the 'eg' GatewayClass resource exists in the cluster."""
    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name, verbosity=0):
        return CheckFailed(errors=[f"Could not set kubectl context for cluster '{cluster_name}'"])
    try:
        result = subprocess.run(
            ["kubectl", "get", "gatewayclass", "eg"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            return CheckPassed()
        return CheckFailed(errors=["GatewayClass 'eg' not found"])
    except FileNotFoundError:
        return CheckFailed(errors=["kubectl not found"])


CREATE_GATEWAYCLASS = Step(
    name="create_gatewayclass",
    description="Creates a GatewayClass resource in the Kind cluster",
    perform=lambda **kwargs: create_gatewayclass_in_kind_cluster(**kwargs),
    check=lambda **kwargs: check_gatewayclass_created(**kwargs),
    rollback=None,
    args={'cluster_name': KIND_CLUSTER_NAME},
    perform_flag='create_gatewayclass_only',
    step_kind=None,  # Set as needed
    depends_on=['deploy_gateway_api_implementation']
)
