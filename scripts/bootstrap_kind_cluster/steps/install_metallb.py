import subprocess
from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind
from scripts.bootstrap_kind_cluster.check_result import CheckPassed, CheckFailed, CheckResult
from scripts.common.git import get_git_root
from scripts.kind_cluster.index import KIND_CLUSTER_NAME
from pathlib import Path
import scripts.common.kind as kind_module

def install_metallb(cluster_name: str = KIND_CLUSTER_NAME) -> bool:
    """
    Installs MetalLB to provide LoadBalancer support in Kind.
    
    MetalLB allows LoadBalancer services (like Gateway API) to get real IPs
    that are accessible from the host, eliminating the need for port-forwarding hacks.
    
    Args:
        cluster_name: Name of the Kind cluster
    
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\nInstalling MetalLB for LoadBalancer support...")
    
    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name):
        print(f"✗ Failed to set kubectl context")
        return False
    
    try:
        subprocess.run(
            ["helm", "repo", "add", "metallb", "https://metallb.github.io/metallb"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        subprocess.run(
            ["helm", "repo", "update", "metallb"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except Exception as e:
        print(f"✗ Failed to add MetalLB Helm repository: {e}")
        return False
    
    try:
        subprocess.run(
            ["helm", "upgrade", "--install", "metallb", "metallb/metallb",
             "--namespace", "metallb-system",
             "--create-namespace"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except Exception as e:
        print(f"✗ Failed to install MetalLB via Helm: {e}")
        return False

    try:
        print("  Waiting for MetalLB deployment to be created...")
        import time
        time.sleep(5)
        
        print("  Waiting for MetalLB controller deployment...")
        subprocess.run(
            ["kubectl", "wait", "--namespace", "metallb-system",
             "--for=condition=available", "deployment/metallb-controller",
             "--timeout=90s"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Configure MetalLB with Kind's network range
        # Get Kind network subnet
        result = subprocess.run(
            ["docker", "network", "inspect", "kind", "-f", "{{(index .IPAM.Config 0).Subnet}}"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        subnet = result.stdout.strip()
        
        # Use a small range from the subnet for LoadBalancer IPs
        # e.g., if subnet is 172.19.0.0/16, use 172.19.255.200-172.19.255.250
        import ipaddress
        network = ipaddress.IPv4Network(subnet)
        # Use the last /24 of the network for LoadBalancer IPs
        lb_start = str(network.network_address + (255 << 8) + 200)
        lb_end = str(network.network_address + (255 << 8) + 250)

        repo_root_str = get_git_root()
        if not repo_root_str:
            print("✗ Could not determine git root directory")
            return False
        
        # Deploy MetalLB configuration via Helm chart
        metallb_chart_path = Path(repo_root_str) / "k8s" / "metallb"
        
        helm_command = [
            "helm", "upgrade", "--install",
            "metallb-config", str(metallb_chart_path),
            "--namespace", "metallb-system",
            "--set", f"ipAddressPool.addressRangeStart={lb_start}",
            "--set", f"ipAddressPool.addressRangeEnd={lb_end}",
            "--wait"
        ]
        
        result = subprocess.run(
            helm_command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode != 0:
            print(f"✗ Failed to configure MetalLB via Helm: {result.stderr}")
            return False
        
        print(f"✓ Successfully installed MetalLB with IP range {lb_start}-{lb_end}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to install MetalLB: {e}")
        return False

def check_metallb_installed(cluster_name: str = KIND_CLUSTER_NAME) -> CheckResult:
    """Check that MetalLB controller deployment is available in the cluster."""
    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name, verbosity=0):
        return CheckFailed(errors=[f"Could not set kubectl context for cluster '{cluster_name}'"])
    try:
        result = subprocess.run(
            ["kubectl", "get", "deployment", "metallb-controller",
             "--namespace", "metallb-system"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            return CheckPassed()
        return CheckFailed(errors=["MetalLB controller deployment not found in namespace 'metallb-system'"])
    except FileNotFoundError:
        return CheckFailed(errors=["kubectl not found"])


INSTALL_METALLB = Step(
    name="install_metallb",
    description="Installs MetalLB to provide LoadBalancer support in Kind on Linux via Bridge",
    perform=lambda **kwargs: install_metallb(**kwargs),
    check=lambda **kwargs: check_metallb_installed(**kwargs),
    rollback=None,
    args={'cluster_name': KIND_CLUSTER_NAME},
    perform_flag='install_metallb_only',
    step_kind=StepKind.Required(),
    depends_on=['initialize_kind_cluster'],
)
