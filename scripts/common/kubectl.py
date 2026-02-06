import subprocess


def is_kubectl_installed() -> bool:
    """Check if kubectl is installed."""
    try:
        subprocess.run(["kubectl", "version", "--client"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def create_namespace(namespace: str) -> bool:
    """Create a Kubernetes namespace."""
    if not is_kubectl_installed():
        raise RuntimeError("'kubectl' is not installed or not in PATH")
    
    try:
        subprocess.run(
            ["kubectl", "create", "namespace", namespace],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except subprocess.CalledProcessError as e:
        if "AlreadyExists" in e.stderr.decode():
            return True
        else:
            return False
