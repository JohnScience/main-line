from scripts.bootstrap_kind_cluster.steps_base import Step
from scripts.common.check_result import CheckPassed, CheckFailed, CheckResult
from scripts.kind_cluster.index import KIND_CLUSTER_NAME
import scripts.common.kind as kind_module
import subprocess
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent

def create_gateway_in_kind_cluster(
        cluster_name: str = KIND_CLUSTER_NAME,
        namespace: str = "envoy-gateway-system"
) -> bool:
    """
    Create a Gateway resource in the Kind cluster.
    
    Args:
        cluster_name: Name of the Kind cluster
        namespace: Namespace to create the Gateway
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\nCreating Gateway in Kind cluster '{cluster_name}'...")
    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name):
        print(f"✗ Failed to set kubectl context for Kind cluster '{cluster_name}'")
        return False
    # kubectl wait --timeout=5m -n envoy-gateway-system deployment/envoy-gateway --for=condition=Available
    try:
        subprocess.run(
            ["kubectl", "wait", "--timeout=5m", "-n", namespace, "deployment/envoy-gateway", "--for=condition=Available"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(f"✓ Gateway controller is available")
    except Exception as e:
        print(f"✗ Gateway controller is unavailable: {e}")
        return False
    try:
        subprocess.run(
            ["kubectl", "apply", "-f", str(project_root / "k8s" / "gateway.yaml")],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(f"✓ Successfully created Gateway")
    except Exception as e:
        print(f"✗ Failed to create Gateway: {e}")
        return False
    
    # Wait for Gateway to create the Envoy proxy deployment
    import time
    print(f"Waiting for Envoy proxy deployment to be created...")
    time.sleep(5)
    
    # Enable hostNetwork on the Envoy proxy deployment for Kind port mapping
    try:
        # Find the gateway deployment name
        result = subprocess.run(
            ["kubectl", "get", "deployment", "-n", namespace, "-l", "gateway.envoyproxy.io/owning-gateway-name=main-line-gateway", "-o", "name"],
            check=True,
            capture_output=True,
            text=True,
        )
        deployment_name = result.stdout.strip()
        
        if deployment_name:
            print(f"Enabling hostNetwork on {deployment_name} for Kind port mapping...")
            subprocess.run(
                ["kubectl", "patch", deployment_name, "-n", namespace, "--type", "strategic", 
                 "-p", '{"spec":{"template":{"spec":{"hostNetwork":true}}}}'],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            print(f"✓ Successfully enabled hostNetwork on Envoy proxy deployment")
        else:
            print(f"⚠ Warning: Could not find Envoy proxy deployment")
    except Exception as e:
        print(f"⚠ Warning: Failed to enable hostNetwork on Envoy proxy: {e}")
        print(f"  You may need to manually run: kubectl patch deployment -n {namespace} <deployment-name> --type strategic -p '{{\"spec\":{{\"template\":{{\"spec\":{{\"hostNetwork\":true}}}}}}}}'")
    
    return True

def check_gateway_created(cluster_name: str = KIND_CLUSTER_NAME, **kwargs) -> CheckResult:
    """Check that the 'main-line-gateway' Gateway resource exists in the default namespace."""
    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name, verbosity=0):
        return CheckFailed(errors=[f"Could not set kubectl context for cluster '{cluster_name}'"])
    try:
        result = subprocess.run(
            ["kubectl", "get", "gateway", "main-line-gateway", "--namespace", "default"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            return CheckPassed()
        return CheckFailed(errors=["Gateway 'main-line-gateway' not found in namespace 'default'"])
    except FileNotFoundError:
        return CheckFailed(errors=["kubectl not found"])


CREATE_GATEWAY = Step(
    name="create_gateway",
    description="Creates a Gateway resource in the Kind cluster",
    perform=lambda **kwargs: create_gateway_in_kind_cluster(**kwargs),
    check=lambda **kwargs: check_gateway_created(**kwargs),
    rollback=None,
    args={
        'cluster_name': KIND_CLUSTER_NAME,
        'namespace': 'envoy-gateway-system'
    },
    perform_flag='create_gateway_only',
    step_kind=None,  # Set as needed
    depends_on=['create_gatewayclass']
)
