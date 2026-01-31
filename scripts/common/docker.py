from pathlib import Path
import subprocess
from typing import TypedDict

class BuildOptions(TypedDict):
    tabulation: str
    force_rebuild: bool
    private_registry: str | None  # Format: "localhost:5000" or None

class DockerImageBuildArgs(TypedDict):
    name: str
    dockerfile: str

def is_docker_installed() -> bool:
    """Check if Docker is installed."""
    try:
        subprocess.run(
            ["docker", "--version"],
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

def build_docker_image(img: DockerImageBuildArgs, options: BuildOptions):
    print(f"{options['tabulation']}Preparing to build Docker image: {img['name']} from {img['dockerfile']}...")
    image_exists = docker_image_exists(img["name"])
    if image_exists and not options.get("force_rebuild"):
        print(f"{options['tabulation']}\tDocker image {img['name']} already exists. Skipping build.")
        return

    if image_exists:
        if not options.get("force_rebuild"):
            print(f"{options['tabulation']}\tDocker image {img['name']} already exists. Skipping build.")
            return
        print(f"{options['tabulation']}\tRemoving existing Docker image: {img['name']}...")
        remove_docker_image(img["name"])

    print(f"{options['tabulation']}\tBuilding Docker image: {img['name']} from {img['dockerfile']}...")
    args = ["docker", "build", "-f", img["dockerfile"], "-t", img["name"]]
    
    # If private registry is specified, also tag with registry name during build
    if options.get("private_registry"):
        registry_name = get_registry_tagged_name(img["name"], options["private_registry"])
        args.extend(["-t", registry_name])
    
    if "build_args" in img and img["build_args"] is not None:
        for arg_key, arg_value in img["build_args"].items():
            args.extend(["--build-arg", f"{arg_key}={arg_value}"])
    args.append(".")
    subprocess.run(
        args,
        check=True
    )

def docker_image_exists(img_name: str) -> bool:
    # silence stdout
    result = subprocess.run(
        ["docker", "images", "-q", img_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return result.stdout.strip() != ""

def remove_docker_image(img_name: str):
    subprocess.run(
        ["docker", "rmi", img_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

def create_container(img_name: str, container_name: str | None = None, on_start: str = "true"):
    if container_name is None:
        container_name = img_name
    subprocess.run(
        ["docker", "container", "create", "--name", container_name, img_name, on_start],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True
    )

def remove_container(container_name: str):
    subprocess.run(
        ["docker", "container", "rm", "-f", container_name],
        stdout=subprocess.PIPE,
    )

def copy_from_container(container_name: str, src_path: str, dest_path: Path):
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["docker", "cp", f"{container_name}:{src_path}", dest_path],
        stdout=subprocess.PIPE,
        check=True
    )

def is_container_running(container_name: str) -> bool:
    """
    Check if a Docker container is running.
    
    Args:
        container_name: Name of the container to check
    
    Returns:
        bool: True if container is running, False otherwise
    """
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        return container_name in result.stdout
    except Exception:
        return False

def container_exists(container_name: str) -> bool:
    """
    Check if a Docker container exists (running or stopped).
    
    Args:
        container_name: Name of the container to check
    
    Returns:
        bool: True if container exists, False otherwise
    """
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        return container_name in result.stdout
    except Exception:
        return False

def get_registry_tagged_name(local_name: str, registry: str) -> str:
    """
    Convert a local image name to a registry-tagged name.
    
    Args:
        local_name: Local image name (e.g., "main-line-backend")
        registry: Registry address (e.g., "localhost:5000")
    
    Returns:
        str: Registry-tagged image name (e.g., "localhost:5000/main-line-backend")
    """
    return f"{registry}/{local_name}"

def tag_image(source_image: str, target_image: str) -> None:
    """
    Tag a Docker image with a new name.
    
    Args:
        source_image: Source image name
        target_image: Target image name (e.g., with registry prefix)
    """
    subprocess.run(
        ["docker", "tag", source_image, target_image],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

def push_image(image: str) -> None:
    """
    Push a Docker image to a registry.
    
    Args:
        image: Full image name including registry (e.g., "localhost:5000/main-line-backend")
    """
    subprocess.run(
        ["docker", "push", image],
        check=True
    )

def pull_image(image: str) -> None:
    """
    Pull a Docker image from a registry.
    
    Args:
        image: Full image name including registry (e.g., "localhost:5000/main-line-backend")
    """
    subprocess.run(
        ["docker", "pull", image],
        check=True
    )

def network_exists(network_name: str) -> bool:
    """
    Check if a Docker network exists.
    
    Args:
        network_name: Name of the network to check
    
    Returns:
        bool: True if network exists, False otherwise
    """
    try:
        result = subprocess.run(
            ["docker", "network", "ls", "--filter", f"name=^{network_name}$", "--format", "{{.Name}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        return network_name in result.stdout
    except Exception:
        return False

def connect_container_to_network(container_name: str, network_name: str) -> None:
    """
    Connect a Docker container to a network.
    
    Args:
        container_name: Name of the container to connect
        network_name: Name of the network to connect to
    
    Raises:
        subprocess.CalledProcessError: If the connection fails
    """
    subprocess.run(
        ["docker", "network", "connect", network_name, container_name],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

def is_container_connected_to_network(container_name: str, network_name: str) -> bool:
    """
    Check if a container is connected to a specific network.
    
    Args:
        container_name: Name of the container
        network_name: Name of the network
    
    Returns:
        bool: True if connected, False otherwise
    """
    try:
        result = subprocess.run(
            ["docker", "network", "inspect", network_name, "--format", "{{range .Containers}}{{.Name}} {{end}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        return container_name in result.stdout.split()
    except Exception:
        return False
