import subprocess
from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind, CliArg, Output
from scripts.common.check_result import CheckPassed, CheckFailed
from scripts.common.docker import (
    container_exists,
    docker_image_exists,
    is_container_running,
    remove_container,
)

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

START_REGISTRY = Step(
    name="start_registry",
    description="Starts a private Docker registry for the main-line project",
    check=lambda **kwargs: CheckPassed() if is_container_running("main-line-registry") else CheckFailed(errors=["Registry container 'main-line-registry' is not running"]),
    perform=lambda **kwargs: run_registry_container(**kwargs),
    rollback=lambda **kwargs: cleanup_registry(**kwargs),
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
)
