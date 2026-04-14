import subprocess
from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind, CliArg, Output
from scripts.common.check_result import CheckPassed, CheckFailed, CheckResult
from scripts.kind_cluster.index import KIND_CLUSTER_NAME
import scripts.common.kind as kind_module

def install_gateway_api_crds(
        cluster_name: str = KIND_CLUSTER_NAME,
        verbosity: int = 1
) -> bool:
    """
    Install the Gateway API CRDs into the Kind cluster.
    
    Args:
        cluster_name: Name of the Kind cluster
    
    Returns:
        bool: True if successful, False otherwise
    """

    if verbosity > 0:
        print(f"\nInstalling Gateway API CRDs into Kind cluster '{cluster_name}'...")
    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name):
        if verbosity > 0:
            print(f"✗ Failed to set kubectl context for Kind cluster '{cluster_name}'")
        return False
    
    try:
        subprocess.run(
            ["kubectl", "apply", "-f", "https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.4.1/standard-install.yaml"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if verbosity > 0:
            print(f"✓ Successfully installed Gateway API CRDs")
        return True
    except Exception as e:
        if verbosity > 0:
            print(f"✗ Failed to install Gateway API CRDs: {e}")
        return False

def check_gateway_api_crds_installed(cluster_name: str = KIND_CLUSTER_NAME) -> CheckResult:
    """Check that the Gateway API CRDs are present in the cluster."""
    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name, verbosity=0):
        return CheckFailed(errors=[f"Could not set kubectl context for cluster '{cluster_name}'"])
    try:
        result = subprocess.run(
            ["kubectl", "get", "crd", "gatewayclasses.gateway.networking.k8s.io"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            return CheckPassed()
        return CheckFailed(errors=["Gateway API CRD 'gatewayclasses.gateway.networking.k8s.io' not found"])
    except FileNotFoundError:
        return CheckFailed(errors=["kubectl not found"])

INSTALL_GATEWAY_API_CRDS = Step(
    name="install_gateway_api_crds",
    description="Installs the Gateway API CRDs into the Kind cluster",
    perform=lambda **kwargs: install_gateway_api_crds(**kwargs),
    check=lambda **kwargs: check_gateway_api_crds_installed(**kwargs),
    rollback=None,
    args={'cluster_name': KIND_CLUSTER_NAME},
    perform_flag='install_gateway_api_crds_only',
    step_kind=StepKind.Required(),
    depends_on=['initialize_kind_cluster'],
)
