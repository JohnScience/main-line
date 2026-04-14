import subprocess
from scripts.kind_cluster.index import KIND_CLUSTER_NAME
import scripts.common.kind as kind_module
import scripts.common.helm as helm_module
from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind
from scripts.common.check_result import CheckPassed, CheckFailed, CheckResult

def deploy_envoy_gateway_in_kind_cluster(
        cluster_name: str = KIND_CLUSTER_NAME,
        namespace: str = "envoy-gateway-system"
) -> bool:
    """
    Deploy Envoy Gateway as the Gateway API implementation in the Kind cluster.
    
    Args:
        cluster_name: Name of the Kind cluster
        namespace: Namespace to deploy Envoy Gateway
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\nDeploying Envoy Gateway in Kind cluster '{cluster_name}'...")
    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name):
        print(f"✗ Failed to set kubectl context for Kind cluster '{cluster_name}'")
        return False
    
    if not helm_module.deploy_envoy_gateway_via_helm(namespace=namespace):
        print(f"✗ Failed to deploy Envoy Gateway via Helm in Kind cluster '{cluster_name}'")
        return False
    
    print(f"✓ Successfully deployed Envoy Gateway in Kind cluster '{cluster_name}'")
    return True

def check_envoy_gateway_deployed(cluster_name: str = KIND_CLUSTER_NAME, namespace: str = 'envoy-gateway-system', **kwargs) -> CheckResult:
    """Check that the Envoy Gateway deployment is present in the cluster."""
    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name, verbosity=0):
        return CheckFailed(errors=[f"Could not set kubectl context for cluster '{cluster_name}'"])
    try:
        result = subprocess.run(
            ["kubectl", "get", "deployment", "envoy-gateway",
             "--namespace", namespace],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            return CheckPassed()
        return CheckFailed(errors=[f"Envoy Gateway deployment not found in namespace '{namespace}'"])
    except FileNotFoundError:
        return CheckFailed(errors=["kubectl not found"])


DEPLOY_GATEWAY_API_IMPLEMENTATION = Step(
    name="deploy_gateway_api_implementation",
    description="Deploys a Gateway API implementation (Envoy Gateway) into the Kind cluster",
    perform=lambda **kwargs: deploy_envoy_gateway_in_kind_cluster(**kwargs),
    check=lambda **kwargs: check_envoy_gateway_deployed(**kwargs),
    rollback=None,
    args={
        'cluster_name': KIND_CLUSTER_NAME,
        'namespace': 'envoy-gateway-system'
    },
    perform_flag='deploy_gateway_api_implementation_only',
    step_kind=StepKind.Required(),
    depends_on=['install_gateway_api_crds'],
)
