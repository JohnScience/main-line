"""
Utilities for interacting with Kind (Kubernetes in Docker).
"""

import subprocess
from pathlib import Path

from .git import get_git_root


def is_kind_installed() -> bool:
    """
    Check if kind is installed and available in PATH.
    
    Returns:
        bool: True if kind is installed, False otherwise
    """
    try:
        result = subprocess.run(
            ["kind", "version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def initialize_kind_cluster(
        cluster_name: str,
        config_path: Path | None = None
    ) -> bool:
    """
    Initializes a Kind cluster, possibly with configuration from the project.
    
    Args:
        cluster_name: Name of the Kind cluster
        config_path: Optional path to the Kind configuration file. 
                     If not provided, Kind will use its default configuration.
    
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\nInitializing Kind cluster '{cluster_name}'...")
    
    # Validate config path if provided
    if config_path is not None:
        if not config_path.exists():
            print(f"✗ Kind config file not found at: {config_path}")
            return False
        print(f"Using config file: {config_path}")
    else:
        print("Using Kind default configuration")
    
    # Check if kind is installed
    if not is_kind_installed():
        print("✗ 'kind' is not installed or not in PATH")
        print("  Install from: https://kind.sigs.k8s.io/docs/user/quick-start/#installation")
        return False
    
    try:
        # Check if cluster already exists
        result = subprocess.run(
            ["kind", "get", "clusters"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        if cluster_name in result.stdout:
            print(f"ℹ Cluster '{cluster_name}' already exists")
            return True
        
        # Create the cluster
        print(f"Creating Kind cluster '{cluster_name}'...")
        cmd = ["kind", "create", "cluster", "--name", cluster_name]
        if config_path is not None:
            cmd.extend(["--config", str(config_path)])
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print(f"✓ Successfully created Kind cluster '{cluster_name}'")
            print(result.stdout)
            return True
        else:
            print(f"✗ Failed to create Kind cluster")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"✗ Failed to initialize Kind cluster: {e}")
        return False


def cleanup_kind_cluster(cluster_name: str) -> bool:
    """
    Delete a Kind cluster.
    
    Args:
        cluster_name: Name of the Kind cluster
    
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\nDeleting Kind cluster '{cluster_name}'...")
    
    # Check if kind is installed
    if not is_kind_installed():
        print("✗ 'kind' is not installed or not in PATH")
        return False
    
    try:
        # Check if cluster exists
        result = subprocess.run(
            ["kind", "get", "clusters"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        if cluster_name not in result.stdout:
            print(f"ℹ Cluster '{cluster_name}' does not exist")
            return True
        
        # Delete the cluster
        result = subprocess.run(
            ["kind", "delete", "cluster", "--name", cluster_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print(f"✓ Successfully deleted Kind cluster '{cluster_name}'")
            return True
        else:
            print(f"✗ Failed to delete Kind cluster")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"✗ Failed to delete Kind cluster: {e}")
        return False

def set_kubectl_context_for_kind_cluster(cluster_name: str) -> bool:
    """
    Sets the kubectl context to the specified Kind cluster.
    
    Args:
        cluster_name: Name of the Kind cluster
    
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\nSetting kubectl context to Kind cluster '{cluster_name}'...")
    
    # Check if kind is installed
    if not is_kind_installed():
        print("✗ 'kind' is not installed or not in PATH")
        return False
    
    try:
        context_name = f"kind-{cluster_name}"
        result = subprocess.run(
            ["kubectl", "config", "use-context", context_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print(f"✓ Successfully set kubectl context to '{context_name}'")
            return True
        else:
            print(f"✗ Failed to set kubectl context")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"✗ Failed to set kubectl context: {e}")
        return False
    
