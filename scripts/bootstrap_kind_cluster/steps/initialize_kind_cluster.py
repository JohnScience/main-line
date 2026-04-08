from pathlib import Path

from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind
from scripts.bootstrap_kind_cluster.check_result import CheckPassed, CheckFailed
from scripts.common.git import get_git_root
from scripts.common import kind as kind_module
from scripts.common.kind import kind_cluster_exists
from scripts.kind_cluster.index import KIND_CLUSTER_NAME

def initialize_kind_cluster(cluster_name: str = KIND_CLUSTER_NAME) -> bool:
    """
    Initialize a Kind cluster using the project's configuration file.
    
    This wrapper function uses the config file at:
    <git-root>/public-configs/kind/kind-config.yaml
    
    Args:
        cluster_name: Name of the Kind cluster
    
    Returns:
        bool: True if successful, False otherwise
    """
    git_root = get_git_root()
    if not git_root:
        print("✗ Could not determine git root directory")
        return False
    
    config_path = Path(git_root) / "public-configs" / "kind" / "kind-config.yaml"
    return kind_module.initialize_kind_cluster(cluster_name, config_path)

def cleanup_kind_cluster(cluster_name: str = KIND_CLUSTER_NAME) -> bool:
    """
    Delete a Kind cluster.
    
    Args:
        cluster_name: Name of the Kind cluster
    
    Returns:
        bool: True if successful, False otherwise
    """
    return kind_module.cleanup_kind_cluster(cluster_name)

INITIALIZE_KIND_CLUSTER = Step(
    name="initialize_kind_cluster",
    description="Uses 'kind' Kubernetes cluster provider to initialize a cluster with a config file",
    perform=lambda **kwargs: initialize_kind_cluster(**kwargs),
    check=lambda cluster_name=KIND_CLUSTER_NAME, **kwargs: CheckPassed() if kind_cluster_exists(cluster_name) else CheckFailed(errors=[f"Kind cluster '{cluster_name}' does not exist"]),
    rollback=lambda **kwargs: cleanup_kind_cluster(**kwargs),
    args={'cluster_name': KIND_CLUSTER_NAME},
    perform_flag='initialize_cluster_only',
    rollback_flag='cleanup_cluster',
    step_kind=StepKind.Required()
)
