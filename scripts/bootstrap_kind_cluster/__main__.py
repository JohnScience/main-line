#!/usr/bin/env python3
"""
Main entry point for bootstrap_kind_cluster.

This module contains the main execution logic and step implementations
for bootstrapping a Kind cluster with a local Docker registry.
"""

import subprocess
import argparse
import sys
import yaml
from pathlib import Path

# Add project root to path to support both direct execution and module import
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import scripts.common.kind as kind_module
import scripts.common.helm as helm_module

from scripts.bootstrap_kind_cluster.steps import Step, StepKind, StepContext, CliArg, Output

from scripts.common.docker import (
    BuildOptions,
    connect_container_to_network,
    container_exists,
    docker_image_exists,
    get_registry_tagged_name,
    is_container_connected_to_network,
    is_container_running,
    network_exists,
    push_image,
    remove_container,
    remove_docker_image,
    tag_image,
)
from scripts.common.docker_images import (
    DOCKER_IMAGES,
    build_all_images,
    extract_artifact,
    PurposeSpecificDataVariant,
)
from scripts.common.git import get_git_root
from scripts.bootstrap_kind_cluster.steps import Step, StepKind, StepContext, CliArg
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


def run_registry_container(port: int | None = None) -> tuple[bool, list[Output]]:
    """
    Run a Docker registry container with the specified port.
    
    If the container already exists, it will be removed and recreated.
    
    Args:
        port: Port to expose the registry on. If None, will prompt user.
    
    Returns:
        tuple[bool, list[Output]]: Success status and list of outputs
    """
    container_name = "main-line-registry"
    image = "registry:2"
    
    # Prompt for port if not provided
    if port is None:
        while True:
            port_input = input(f"Enter port for Docker registry (default: 5000): ").strip()
            if not port_input:
                port = 5000
                break
            try:
                port = int(port_input)
                if 1 <= port <= 65535:
                    break
                else:
                    print("Port must be between 1 and 65535")
            except ValueError:
                print("Invalid port number. Please enter a valid integer.")
    
    print(f"\nSetting up Docker registry on port {port}...")
    
    # Remove existing container if it exists
    if container_exists(container_name):
        print(f"Removing existing container '{container_name}'...")
        remove_container(container_name)
    
    try:
        # Pull the registry image if it doesn't exist
        if not docker_image_exists(image):
            print(f"Pulling {image} image...")
            subprocess.run(
                ["docker", "pull", image],
                check=True
            )
        else:
            print(f"Image {image} already exists locally")
        
        # Run the registry container
        print(f"Starting registry container '{container_name}'...")
        subprocess.run(
            [
                "docker", "run", "-d",
                "--name", container_name,
                "-p", f"{port}:5000",
                "--restart=always",
                image
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Verify the container is running
        if is_container_running(container_name):
            print(f"✓ Registry container started successfully on port {port}")
            print(f"  Access it at: http://localhost:{port}")
            outputs = [
                Output(
                    title="Registry Started",
                    body=f"localhost:{port}"
                )
            ]
            return True, outputs
        else:
            print(f"✗ Container was created but is not running")
            return False, []
            
    except Exception as e:
        print(f"✗ Failed to start registry container: {e}")
        return False, []


def build_and_push_all_images(registry_host: str, registry_port: int, force_rebuild: bool = False) -> bool:
    """
    Build all Docker images, tag them for the registry, and push them.
    
    Workflow:
    1. Build all images in dependency order using docker_images.build_all_images()
    2. Push each built image to the private registry
    3. Extract artifacts from data-only images
    
    Args:
        registry_host: Registry hostname (e.g., "localhost")
        registry_port: Registry port number
        force_rebuild: Whether to force rebuild existing images
    
    Returns:
        bool: True if all operations successful, False otherwise
    """
    print("\n=== Building and Pushing All Images ===")
    
    registry = f"{registry_host}:{registry_port}"
    
    # Build all images with registry tagging
    build_options: BuildOptions = {
        "tabulation": "",
        "force_rebuild": force_rebuild,
        "private_registry": registry,
    }
    
    try:
        print(f"\nBuilding images (tagged for {registry})...")
        built_images = build_all_images(build_options)
        
        if not built_images:
            print("✗ No images were built")
            return False
        
        # Tag and push all images to the registry
        print(f"\nTagging and pushing {len(built_images)} images to registry...")
        for image_name in built_images:
            registry_image = get_registry_tagged_name(image_name, registry)
            
            try:
                # Tag the image for the registry if not already tagged during build
                if not docker_image_exists(registry_image):
                    print(f"  Tagging {image_name} as {registry_image}...")
                    tag_image(image_name, registry_image)
                
                # Push to registry
                print(f"  Pushing {registry_image}...")
                push_image(registry_image)
                print(f"  ✓ Successfully pushed {registry_image}")
            except Exception as e:
                print(f"  ✗ Failed to push {registry_image}: {e}")
                return False
        
        # Extract artifacts from data-only images
        print("\nExtracting artifacts from data-only images...")
        data_only_images = [
            img for img in DOCKER_IMAGES 
            if img["name"] is not None 
            and isinstance(img["purpose_specific_data"], PurposeSpecificDataVariant.DataOnly)
        ]
        
        if data_only_images:
            for img in data_only_images:
                try:
                    extract_artifact(img, "  ")
                except Exception as e:
                    print(f"  ⚠ Warning: Failed to extract artifact from {img['name']}: {e}")
                    # Don't fail the entire process for artifact extraction failures
        else:
            print("  No data-only images to extract artifacts from.")
        
        print(f"\n✓ Successfully built and pushed all {len(built_images)} images to {registry}")
        return True
        
    except Exception as e:
        print(f"\n✗ Failed to build and push images: {e}")
        return False


def cleanup_registry(container_name: str = "main-line-registry") -> bool:
    """
    Stop and remove the registry container.
    
    Args:
        container_name: Name of the registry container
    
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\nCleaning up registry container '{container_name}'...")
    
    try:
        if container_exists(container_name):
            remove_container(container_name)
            print(f"✓ Removed registry container '{container_name}'")
            return True
        else:
            print(f"ℹ Registry container '{container_name}' does not exist")
            return True
    except Exception as e:
        print(f"✗ Failed to remove registry container: {e}")
        return False


def cleanup_images(registry_host: str = "localhost", registry_port: int = 5000) -> bool:
    """
    Remove locally built images (both local and registry-tagged versions).
    
    Args:
        registry_host: Registry hostname
        registry_port: Registry port number
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("\nCleaning up Docker images...")
    
    registry = f"{registry_host}:{registry_port}"
    removed_count = 0
    failed_count = 0
    
    for img in DOCKER_IMAGES:
        if img["name"] is None:
            continue
        
        local_name = img["name"]
        registry_name = get_registry_tagged_name(local_name, registry)
        
        # Remove registry-tagged image
        if docker_image_exists(registry_name):
            try:
                remove_docker_image(registry_name)
                print(f"  ✓ Removed {registry_name}")
                removed_count += 1
            except Exception as e:
                print(f"  ✗ Failed to remove {registry_name}: {e}")
                failed_count += 1
        
        # Remove local image
        if docker_image_exists(local_name):
            try:
                remove_docker_image(local_name)
                print(f"  ✓ Removed {local_name}")
                removed_count += 1
            except Exception as e:
                print(f"  ✗ Failed to remove {local_name}: {e}")
                failed_count += 1
    
    if removed_count > 0:
        print(f"\n✓ Removed {removed_count} images")
    else:
        print("\nℹ No images found to remove")
    
    if failed_count > 0:
        print(f"⚠ Failed to remove {failed_count} images")
        return False
    
    return True


def cleanup_all(container_name: str = "main-line-registry", registry_host: str = "localhost", registry_port: int = 5000) -> bool:
    """
    Complete cleanup: remove registry container and all built images.
    
    Args:
        container_name: Name of the registry container
        registry_host: Registry hostname
        registry_port: Registry port number
    
    Returns:
        bool: True if all cleanup successful, False otherwise
    """
    print("=== Cleaning Up Bootstrap Setup ===")
    
    success = True
    
    # Clean up images first (while registry might still be running)
    if not cleanup_images(registry_host, registry_port):
        success = False
    
    # Then clean up registry
    if not cleanup_registry(container_name):
        success = False
    
    if success:
        print("\n✓ Cleanup complete!")
    else:
        print("\n⚠ Cleanup completed with some errors")
    
    return success


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


def install_gateway_api_crds(cluster_name: str = KIND_CLUSTER_NAME) -> bool:
    """
    Install the Gateway API CRDs into the Kind cluster.
    
    Args:
        cluster_name: Name of the Kind cluster
    
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\nInstalling Gateway API CRDs into Kind cluster '{cluster_name}'...")
    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name):
        print(f"✗ Failed to set kubectl context for Kind cluster '{cluster_name}'")
        return False
    
    try:
        subprocess.run(
            ["kubectl", "apply", "-f", "https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.4.1/standard-install.yaml"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(f"✓ Successfully installed Gateway API CRDs")
        return True
    except Exception as e:
        print(f"✗ Failed to install Gateway API CRDs: {e}")
        return False

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


def deploy_kubernetes_dashboard(cluster_name: str = KIND_CLUSTER_NAME) -> bool:
    """
    Deploy the Kubernetes Dashboard in the specified Kind cluster.
    
    Args:
        cluster_name: Name of the Kind cluster
    
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\nDeploying Kubernetes Dashboard in Kind cluster '{cluster_name}'...")
    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name):
        print(f"✗ Failed to set kubectl context for Kind cluster '{cluster_name}'")
        return False
    
    if not helm_module.deploy_kubernetes_dashboard_via_helm():
        print(f"✗ Failed to deploy Kubernetes Dashboard via Helm in Kind cluster '{cluster_name}'")
        return False
    
    print(f"✓ Successfully deployed Kubernetes Dashboard in Kind cluster '{cluster_name}'")
    return True


def create_kubernetes_dashboard_admin(cluster_name: str = KIND_CLUSTER_NAME) -> bool:
    """
    Creates the service account and cluster role binding for the Kubernetes Dashboard admin user.
    
    Args:
        cluster_name: Name of the Kind cluster
    
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\nCreating Kubernetes Dashboard admin user...")

    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name):
        print(f"✗ Failed to set kubectl context for Kind cluster '{cluster_name}'")
        return False
    
    try:
        subprocess.run(
            ["kubectl", "apply", "-f", str(project_root / "k8s" / "kubernetes-dashboard" / "kubernetes-dashboard-admin.yaml")],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(f"✓ Successfully created Kubernetes Dashboard admin user service account")
    except Exception as e:
        print(f"✗ Failed to create Kubernetes Dashboard admin user service account: {e}")
        return False
    
    try:
        subprocess.run(
            ["kubectl", "apply", "-f", str(project_root / "k8s" / "base" / "cluster-admin-role-binding.yaml")],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(f"✓ Successfully created ClusterRoleBinding for admin user")
        return True
    except Exception as e:
        print(f"✗ Failed to create ClusterRoleBinding for admin user: {e}")
        return False

def create_kubernetes_dashboard_httproute(cluster_name: str = KIND_CLUSTER_NAME) -> tuple[bool, list[Output]]:
    """
    Creates the HTTPRoute for the Kubernetes Dashboard via Helm.
    This allows dynamic configuration of hostnames including the Gateway IP.
    
    Args:
        cluster_name: Name of the Kind cluster
    Returns:
        tuple[bool, list[Output]]: Success status and list of outputs
    """
    print(f"\nCreating Kubernetes Dashboard HTTPRoute...")

    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name):
        print(f"✗ Failed to set kubectl context for Kind cluster '{cluster_name}'")
        return False, []
    
    try:
        # Read the dashboard port from gateway.yaml
        gateway_yaml_path = project_root / "k8s" / "gateway.yaml"
        dashboard_port = None
        try:
            with open(gateway_yaml_path, 'r') as f:
                gateway_config = yaml.safe_load(f)
                listeners = gateway_config.get('spec', {}).get('listeners', [])
                for listener in listeners:
                    if listener.get('name') == 'dashboard-direct':
                        dashboard_port = listener.get('port')
                        break
        except Exception as e:
            print(f"✗ Failed to read port from gateway.yaml: {e}")
            return False, []
        
        if dashboard_port is None:
            print(f"✗ Failed to find 'dashboard-direct' listener port in gateway.yaml")
            return False, []
        
        # Read the HTTPRoute chart path from values.yaml
        httproute_values_path = project_root / "k8s" / "kubernetes-dashboard" / "httproute" / "values.yaml"
        gateway_name = None
        gateway_namespace = None
        dashboard_hostnames = []
        try:
            with open(httproute_values_path, 'r') as f:
                httproute_config = yaml.safe_load(f)
                gateway_name = httproute_config.get('gateway', {}).get('name')
                gateway_namespace = httproute_config.get('gateway', {}).get('namespace')
                dashboard_hostnames = httproute_config.get('hostnames', {}).get('domain', [])
        except Exception as e:
            print(f"✗ Failed to read gateway configuration from httproute values.yaml: {e}")
            return False, []
        
        if not gateway_name or not gateway_namespace:
            print(f"✗ Failed to find gateway name or namespace in httproute values.yaml")
            return False, []
        
        if not dashboard_hostnames:
            print(f"✗ Failed to find dashboard hostnames in httproute values.yaml")
            return False, []
        
        # Use the first hostname as the primary dashboard URL
        primary_hostname = dashboard_hostnames[0]
        
        # Get the Gateway LoadBalancer IP
        result = subprocess.run(
            ["kubectl", "get", "gateway", gateway_name, "-n", gateway_namespace,
             "-o", "jsonpath={.status.addresses[0].value}"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        gateway_ip = result.stdout.strip()
        
        if not gateway_ip:
            print("⚠ Warning: Gateway LoadBalancer IP not yet assigned, deploying without IP hostname")
            gateway_ip_arg = []
        else:
            gateway_ip_arg = ["--set", f"hostnames.gatewayIP={gateway_ip}"]
        
        # Deploy HTTPRoute via Helm
        httproute_chart_path = project_root / "k8s" / "kubernetes-dashboard" / "httproute"
        
        helm_command = [
            "helm", "upgrade", "--install",
            "kubernetes-dashboard-httproute", str(httproute_chart_path),
            "--namespace", "kubernetes-dashboard",
            "--create-namespace"
        ] + gateway_ip_arg
        
        subprocess.run(
            helm_command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Deploy direct access HTTPRoute (for localhost:<port>)
        try:
            subprocess.run(
                ["kubectl", "apply", "-f", str(project_root / "k8s" / "kubernetes-dashboard" / "httproute-direct.yaml")],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception as e:
            print(f"⚠ Warning: Failed to create direct access HTTPRoute: {e}")
        
        if gateway_ip:
            print(f"✓ Successfully created Kubernetes Dashboard HTTPRoute (accessible via {primary_hostname}, {gateway_ip}, and localhost:{dashboard_port})")
            outputs = [
                Output(
                    title="Dashboard URL",
                    body=f"http://{primary_hostname} (Gateway IP: {gateway_ip}), http://localhost:{dashboard_port}"
                )
            ]
        else:
            print(f"✓ Successfully created Kubernetes Dashboard HTTPRoute (accessible via {primary_hostname} and localhost:{dashboard_port})")
            outputs = [
                Output(
                    title="Dashboard URL",
                    body=f"http://{primary_hostname}, http://localhost:{dashboard_port}"
                )
            ]
        return True, outputs
    except Exception as e:
        print(f"✗ Failed to create Kubernetes Dashboard HTTPRoute: {e}")
        return False, []


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

# Define all available steps
ALL_STEPS = [
    Step(
        name="start_registry",
        description="Starts a private Docker registry for the main-line project",
        perform=lambda **kwargs: run_registry_container(**kwargs),
        rollback=lambda **kwargs: cleanup_registry(),
        args={'port': 5000},
        perform_flag='registry_only',
        rollback_flag='cleanup_registry',
        step_kind=StepKind.Required(),
        cli_arg_mappings={'port': 'port'},
        cli_args=[
            CliArg(
                name='port',
                arg_type=int,
                default=5000,
                help='Registry port',
                step_description='Port to expose the Docker registry on'
            )
        ]
    ),
    Step(
        name="build_and_push_images",
        description="Builds and pushes all Docker images to the private registry so that they can be accessed by the 'kind'-powered cluster",
        perform=lambda **kwargs: build_and_push_all_images(**kwargs),
        rollback=lambda registry_host='localhost', registry_port=5000, **kwargs: cleanup_images(registry_host, registry_port),
        args={
            'registry_host': 'localhost',
            'registry_port': 5000,
            'force_rebuild': False
        },
        rollback_flag='cleanup_images',
        step_kind=StepKind.Optional(skip_flag='skip_build'),
        cli_arg_mappings={'registry_port': 'port', 'force_rebuild': 'force_rebuild'},
        cli_args=[
            CliArg(
                name='port',
                arg_type=int,
                default=5000,
                help='Registry port',
                step_description='Registry port for pushing built images'
            ),
            CliArg(
                name='force_rebuild',
                arg_type=bool,
                default=False,
                help='Force rebuild Docker images',
                step_description='Rebuild all images even if they already exist'
            )
        ],
        depends_on=['start_registry']
    ),
    Step(
        name="initialize_kind_cluster",
        description="Uses 'kind' Kubernetes cluster provider to initialize a cluster with a config file",
        perform=lambda **kwargs: initialize_kind_cluster(**kwargs),
        rollback=lambda **kwargs: cleanup_kind_cluster(**kwargs),
        args={'cluster_name': KIND_CLUSTER_NAME},
        perform_flag='initialize_cluster_only',
        rollback_flag='cleanup_cluster',
        step_kind=StepKind.Required()
    ),
    Step(
        name="connect_to_kind",
        description="Connects the private Docker registry to the 'kind' network ('docker network connect kind main-line-registry')",
        perform=lambda **kwargs: connect_registry_to_kind_network(**kwargs),
        rollback=None,
        args={'registry_name': 'main-line-registry', 'cluster_name': KIND_CLUSTER_NAME},
        perform_flag='connect_to_kind_only',
        step_kind=StepKind.Required(),
        depends_on=['initialize_kind_cluster', 'start_registry'],
    ),
    Step(
        name="install_gateway_api_crds",
        description="Installs the Gateway API CRDs into the Kind cluster",
        perform=lambda **kwargs: install_gateway_api_crds(**kwargs),
        rollback=None,
        args={'cluster_name': KIND_CLUSTER_NAME},
        perform_flag='install_gateway_api_crds_only',
        step_kind=StepKind.Required(),
        depends_on=['initialize_kind_cluster'],
    ),
    Step(
        name="install_metallb",
        description="Installs MetalLB to provide LoadBalancer support in Kind on Linux via Bridge",
        perform=lambda **kwargs: install_metallb(**kwargs),
        rollback=None,
        args={'cluster_name': KIND_CLUSTER_NAME},
        perform_flag='install_metallb_only',
        step_kind=StepKind.Required(),
        depends_on=['initialize_kind_cluster'],
    ),
    Step(
        name="deploy_gateway_api_implementation",
        description="Deploys a Gateway API implementation (Envoy Gateway) into the Kind cluster",
        perform=lambda **kwargs: deploy_envoy_gateway_in_kind_cluster(**kwargs),
        rollback=None,
        args={
            'cluster_name': KIND_CLUSTER_NAME,
            'namespace': 'envoy-gateway-system'
        },
        perform_flag='deploy_gateway_api_implementation_only',
        step_kind=StepKind.Required(),
        depends_on=['install_gateway_api_crds'],
    ),
    Step(
        name="create_gatewayclass",
        description="Creates a GatewayClass resource in the Kind cluster",
        perform=lambda **kwargs: create_gatewayclass_in_kind_cluster(**kwargs),
        rollback=None,
        args={'cluster_name': KIND_CLUSTER_NAME},
        perform_flag='create_gatewayclass_only',
        step_kind=StepKind.Required(),
        depends_on=['deploy_gateway_api_implementation']
    ),
    Step(
        name="create_gateway",
        description="Creates a Gateway resource in the Kind cluster",
        perform=lambda **kwargs: create_gateway_in_kind_cluster(**kwargs),
        rollback=None,
        args={
            'cluster_name': KIND_CLUSTER_NAME,
            'namespace': 'envoy-gateway-system'
        },
        perform_flag='create_gateway_only',
        step_kind=StepKind.Required(),
        depends_on=['create_gatewayclass']
    ),
    Step(
        name="deploy_kubernetes_dashboard",
        description="Deploys the Kubernetes Dashboard in the Kind cluster",
        perform=lambda **kwargs: deploy_kubernetes_dashboard(**kwargs),
        rollback=None,
        args={'cluster_name': KIND_CLUSTER_NAME},
        perform_flag='deploy_dashboard_only',
        step_kind=StepKind.Optional(enable_flag='deploy_dashboard'),
        depends_on=['initialize_kind_cluster']
    ),
    Step(
        name="create_kubernetes_dashboard_admin",
        description="Creates the service account and cluster role binding for the Kubernetes Dashboard admin user",
        perform=lambda **kwargs: create_kubernetes_dashboard_admin(**kwargs),
        rollback=None,
        args={'cluster_name': KIND_CLUSTER_NAME},
        perform_flag='create_dashboard_admin_only',
        step_kind=StepKind.Optional(enable_flag='deploy_dashboard'),
        depends_on=['deploy_kubernetes_dashboard']
    ),
    Step(
        name="create_kubernetes_dashboard_httproute",
        description="Creates the HTTPRoute for the Kubernetes Dashboard",
        perform=lambda **kwargs: create_kubernetes_dashboard_httproute(**kwargs),
        rollback=None,
        args={'cluster_name': KIND_CLUSTER_NAME},
        perform_flag="create_kubernetes_dashboard_httproute_only",
        step_kind=StepKind.Optional(enable_flag='deploy_dashboard'),
        depends_on=['create_gateway', 'create_kubernetes_dashboard_admin']
    ),
    Step(
        name="add_grafana_chart_repo",
        description="Adds the Grafana Helm chart repository",
        perform=lambda **kwargs: helm_module.add_grafana_helm_repo(),
        rollback=None,
        step_kind=StepKind.Required(),
        depends_on=['initialize_kind_cluster']
    ),
    Step(
        name="deploy_loki",
        description="Deploys Loki for log aggregation in the Kind cluster",
        perform=lambda **kwargs: helm_module.deploy_loki_via_helm(),
        rollback=None,
        step_kind=StepKind.Required(),
        perform_flag="deploy_loki_only",
        depends_on=['initialize_kind_cluster', 'add_grafana_chart_repo']
    )
]


def main():
    description = 'Bootstrap a local Docker registry and Kind cluster for Main-Line development.'
    description += '\n\nAvailable Steps:'

    for step in ALL_STEPS:
        description += f'\n  - \'{step.name}\': {step.description}'

    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Add global arguments
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Global argument. Performs complete cleanup'
    )
    parser.add_argument(
        '--no-rollback',
        action='store_true',
        help='Global argument. Disable automatic rollback on failure'
    )
    
    # Track which CLI args have been added and which steps use them
    # Format: {'--port': [{'step': step_obj, 'cli_arg': cli_arg_obj}, ...]}
    added_args = {}
    
    # First pass: collect all argument usages across steps
    for step in ALL_STEPS:
        for cli_arg in step.cli_args:
            flag_name = cli_arg.get_flag_name()
            if flag_name not in added_args:
                added_args[flag_name] = []
            added_args[flag_name].append({
                'step': step,
                'cli_arg': cli_arg
            })
    
    # Second pass: add arguments to parser with multi-line help
    for flag_name, usages in added_args.items():
        # Get the first usage for type and default info
        first_usage = usages[0]
        cli_arg = first_usage['cli_arg']
        
        # Build multi-line help text
        help_lines = [f"Step-specific argument. {cli_arg.help or f'{cli_arg.name} option'}"]
        
        if len(usages) > 1:
            help_lines[0] += f' [used in {len(usages)} steps]'
        else:
            help_lines[0] += f" [used in step '{usages[0]['step'].name}']"
        
        for usage in usages:
            step_name = usage['step'].name
            step_desc = usage['cli_arg'].step_description or 'used by this step'
            help_lines.append(f"  * In step '{step_name}': {step_desc}")
        
        help_text = '\n'.join(help_lines)
        
        # Add argument to parser
        if cli_arg.arg_type == bool:
            parser.add_argument(
                flag_name,
                action='store_true',
                help=help_text
            )
        else:
            parser.add_argument(
                flag_name,
                type=cli_arg.arg_type,
                default=cli_arg.default,
                help=help_text
            )
    
    # Track flags for skip/enable/perform/rollback (to avoid duplicates)
    added_flags = set(added_args.keys())
    
    # Add step-specific control flags
    for step in ALL_STEPS:
        # Add skip_flag and enable_flag from step_kind
        if isinstance(step.step_kind, StepKind.Optional):
            if step.step_kind.skip_flag:
                flag_name = f'--{step.step_kind.skip_flag.replace("_", "-")}'
                if flag_name not in added_flags:
                    added_flags.add(flag_name)
                    parser.add_argument(
                        flag_name,
                        action='store_true',
                        help=f'Step-specific argument. Skip step \'{step.name}\''
                    )
            if step.step_kind.enable_flag:
                flag_name = f'--{step.step_kind.enable_flag.replace("_", "-")}'
                if flag_name not in added_flags:
                    added_flags.add(flag_name)
                    parser.add_argument(
                        flag_name,
                        action='store_true',
                        help=f'Step-specific argument. Enable step \'{step.name}\''
                    )
        
        # Add perform_flag and rollback_flag
        if step.perform_flag:
            flag_name = f'--{step.perform_flag.replace("_", "-")}'
            if flag_name not in added_flags:
                added_flags.add(flag_name)
                parser.add_argument(flag_name, action='store_true', help=f'Step-specific argument. Only run step \'{step.name}\'')
        
        if step.rollback_flag:
            flag_name = f'--{step.rollback_flag.replace("_", "-")}'
            if flag_name not in added_flags:
                added_flags.add(flag_name)
                parser.add_argument(flag_name, action='store_true', help=f'Step-specific argument. Rollback step \'{step.name}\'')
    
    args = parser.parse_args()
    
    # Handle cleanup operations (check if any step wants to be cleaned up)
    if args.cleanup:
        return 0 if cleanup_all(registry_port=args.port) else 1
    
    # Create a copy of steps and update args from command line
    steps: list[Step] = []
    for step_template in ALL_STEPS:
        step = Step(
            name=step_template.name,
            description=step_template.description,
            perform=step_template.perform,
            rollback=step_template.rollback,
            args=step_template.args.copy(),
            perform_flag=step_template.perform_flag,
            rollback_flag=step_template.rollback_flag,
            step_kind=step_template.step_kind,
            cli_arg_mappings=step_template.cli_arg_mappings,
            cli_args=step_template.cli_args
        )
        
        # Apply CLI argument mappings declaratively
        for step_arg_name, cli_arg_name in step.cli_arg_mappings.items():
            if hasattr(args, cli_arg_name):
                step.args[step_arg_name] = getattr(args, cli_arg_name)
        
        steps.append(step)
    
    # Check if any step should be cleaned up individually
    for step in steps:
        if step.should_rollback(args):
            print(f"=== Cleaning Up: {step.description} ===")
            success = step.undo(force=True)  # Force rollback even if not completed
            return 0 if success else 1
    
    # Check if any step should run exclusively
    for step in steps:
        if step.should_perform_only(args):
            print(f"=== Running Only: {step.description} ===")
            context = StepContext([step], auto_rollback=not args.no_rollback)
            if context.execute_all():
                print(f"\n✓ Step '{step.name}' complete!")
                
                # Print outputs if any
                if context.all_outputs:
                    print("\n" + "=" * 60)
                    print("Step Complete - Important Information:")
                    print("=" * 60)
                    for output in context.all_outputs:
                        print(f"\n{output.title}:")
                        print(f"  {output.body}")
                    print("\n" + "=" * 60)
                
                return 0
            else:
                print(f"\n✗ Step '{step.name}' failed")
                return 1
    
    print("=== Docker Registry and Kind Cluster Setup ===")
    
    # Filter steps based on their kind and flags
    steps_to_run = []
    
    for step in steps:
        should_include = False
        
        if isinstance(step.step_kind, StepKind.Required):
            # Required steps always run (unless skipped via their perform_flag)
            should_include = True
        elif isinstance(step.step_kind, StepKind.Optional):
            # Optional steps run based on their enable/skip flags
            skip_flag = step.step_kind.skip_flag
            enable_flag = step.step_kind.enable_flag
            
            # Default to include if no flags are set
            should_include = True
            
            # Check if explicitly skipped
            if skip_flag and getattr(args, skip_flag, False):
                should_include = False
            # Check if enable flag is required but not set
            elif enable_flag and not getattr(args, enable_flag, False):
                should_include = False
        
        if should_include:
            steps_to_run.append(step)
    
    # Execute all steps
    context = StepContext(steps_to_run, auto_rollback=not args.no_rollback)
    success = context.execute_all()
    
    if not success:
        print("\n✗ Setup failed")
        return 1
    
    # Print all collected outputs
    if context.all_outputs:
        print("\n" + "=" * 60)
        print("Setup Complete - Important Information:")
        print("=" * 60)
        for output in context.all_outputs:
            print(f"\n{output.title}:")
            print(f"  {output.body}")
        print("\n" + "=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
