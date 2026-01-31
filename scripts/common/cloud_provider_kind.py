from ipaddress import IPv4Address, IPv6Address, ip_address
import subprocess
import time
from typing import Optional

from scripts.common.docker import is_docker_installed

def is_cloud_provider_kind_installed() -> bool:
    """Check if the 'cloud-provider-kind' is installed."""
    
    try:
        subprocess.run(
            ["cloud-provider-kind", "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False
    
def await_kindccm_container_id(
    timeout: float = 60.0,
    poll_interval: float = 0.5,
) -> Optional[str]:
    """Wait for the 'kindccm' Docker container to appear and return its ID."""

    if not is_docker_installed():
        raise RuntimeError("'docker' is not installed or not in PATH")
    
    print("Waiting for 'kindccm' Docker container to start...")

    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        try:
            result = subprocess.run(
                ["docker", "ps", "-q", "-f", "name=kindccm"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )

            container_id = result.stdout.strip()
            if container_id:
                return container_id

        except Exception:
            pass

        time.sleep(poll_interval)

    return None
    
def get_exposed_ip_from_kindccm(container_id: str) -> IPv4Address | IPv6Address | None:
    """Get the exposed IP address from the 'kindccm' Docker container."""
    
    try:
        # docker inspect -f "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}" <container-id>
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}", container_id],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        ip_str = result.stdout.strip()
        return ip_address(ip_str) if ip_str else None
    except Exception:
        return None

def expose_kind_cluster_network(cluster_name: str) -> IPv4Address | IPv6Address:
    """
    Expose the network for a kind cluster using 'cloud-provider-kind'.
    
    Args:
        cluster_name (str): The name of the kind cluster.
    Returns:
        IPv4Address | IPv6Address: The exposed IP address.
    """

    if not is_cloud_provider_kind_installed():
        raise RuntimeError("'cloud-provider-kind' is not installed or not in PATH")
    
    if not is_docker_installed():
        raise RuntimeError("'docker' is not installed or not in PATH")
    
    try:
        subprocess.Popen(
            ["sudo", "cloud-provider-kind", "--gateway-channel", "disabled"],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
    except Exception as e:
        raise RuntimeError(f"Failed to start 'cloud-provider-kind': {e}")    
    
    container_id = await_kindccm_container_id()
    if container_id is None:
        raise RuntimeError("Could not find 'kindccm' Docker container")
    return get_exposed_ip_from_kindccm(container_id) or RuntimeError("Could not get exposed IP from 'kindccm' container")

