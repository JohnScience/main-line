from scripts.common.docker import (
    connect_container_to_network,
    container_exists,
    is_container_connected_to_network,
    is_container_running,
    network_exists,
)

from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind
from scripts.bootstrap_kind_cluster.check_result import CheckPassed, CheckFailed
from scripts.kind_cluster.index import KIND_CLUSTER_NAME

def connect_registry_to_kind_network(registry_name: str = "main-line-registry", cluster_name: str = "kind") -> bool:
    """
    Connect the registry container to the Kind cluster's Docker network.
    
    Kind creates a Docker bridge network named 'kind' (or with cluster name prefix).
    By connecting the registry to this network, the Kind cluster can access it.
    
    Args:
        registry_name: Name of the registry container
        cluster_name: Name of the Kind cluster (used to determine network name)
    
    Returns:
        bool: True if successful, False otherwise
    """
    network_name = "kind"  # Default Kind network name
    
    print(f"\nConnecting registry to Kind network...")
    
    # Check if registry container exists and is running
    if not container_exists(registry_name):
        print(f"✗ Registry container '{registry_name}' does not exist")
        return False
    
    if not is_container_running(registry_name):
        print(f"✗ Registry container '{registry_name}' is not running")
        return False
    
    # Check if Kind network exists
    if not network_exists(network_name):
        print(f"✗ Kind network '{network_name}' does not exist")
        print(f"  Make sure a Kind cluster is running (kind create cluster)")
        return False
    
    # Check if already connected
    if is_container_connected_to_network(registry_name, network_name):
        print(f"ℹ Registry is already connected to '{network_name}' network")
        return True
    
    # Connect to network
    try:
        connect_container_to_network(registry_name, network_name)
        print(f"✓ Successfully connected '{registry_name}' to '{network_name}' network")
        print(f"  Kind cluster can now access registry at: {registry_name}:5000")
        return True
    except Exception as e:
        print(f"✗ Failed to connect registry to Kind network: {e}")
        return False

CONNECT_TO_KIND = Step(
    name="connect_to_kind",
    description="Connects the private Docker registry to the 'kind' network ('docker network connect kind main-line-registry')",
    perform=lambda **kwargs: connect_registry_to_kind_network(**kwargs),
    check=lambda registry_name='main-line-registry', **kwargs: CheckPassed() if is_container_connected_to_network(registry_name, "kind") else CheckFailed(errors=[f"Container '{registry_name}' is not connected to the 'kind' network"]),
    rollback=None,
    args={'registry_name': 'main-line-registry', 'cluster_name': KIND_CLUSTER_NAME},
    perform_flag='connect_to_kind_only',
    step_kind=StepKind.Required(),
    depends_on=['initialize_kind_cluster', 'start_registry'],
)
