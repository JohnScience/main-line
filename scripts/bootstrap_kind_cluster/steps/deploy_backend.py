import subprocess
from pathlib import Path

from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind
from scripts.common.check_result import CheckPassed, CheckFailed, CheckResult
import scripts.common.kind as kind_module
from scripts.kind_cluster.index import KIND_CLUSTER_NAME

project_root = Path(__file__).parent.parent.parent.parent


def deploy_backend(cluster_name: str = KIND_CLUSTER_NAME) -> bool:
    """
    Deploy the backend service to the Kind cluster by applying the core manifests
    from k8s/backend/ explicitly.

    Args:
        cluster_name: Name of the Kind cluster
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\nDeploying backend to Kind cluster '{cluster_name}'...")

    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name):
        print(f"✗ Failed to set kubectl context for Kind cluster '{cluster_name}'")
        return False

    backend_dir = project_root / "k8s" / "backend"
    manifests = [
        backend_dir / "namespace.yaml",
        backend_dir / "configmap.yaml",
        backend_dir / "service.yaml",
        backend_dir / "deployment.yaml",
        backend_dir / "httproute.yaml",
    ]

    try:
        result = subprocess.run(
            ["kubectl", "apply"] + [arg for f in manifests for arg in ("-f", str(f))],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print("✓ Successfully applied backend manifests")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to apply backend manifests: {e}")
        if e.stderr:
            print(e.stderr.decode())
        return False

    try:
        subprocess.run(
            [
                "kubectl", "rollout", "status", "deployment/backend",
                "--namespace", "backend",
                "--timeout=2m",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print("✓ Backend deployment is ready")
        return True
    except Exception as e:
        print(f"✗ Backend deployment did not become ready: {e}")
        return False


def check_backend_deployed(cluster_name: str = KIND_CLUSTER_NAME, **kwargs) -> CheckResult:
    """Check that the backend Deployment exists and is available."""
    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name, verbosity=0):
        return CheckFailed(errors=[f"Could not set kubectl context for cluster '{cluster_name}'"])
    try:
        result = subprocess.run(
            ["kubectl", "get", "deployment", "backend", "--namespace", "backend"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            return CheckPassed()
        return CheckFailed(errors=["Deployment 'backend' not found in namespace 'backend'"])
    except FileNotFoundError:
        return CheckFailed(errors=["kubectl not found"])


DEPLOY_BACKEND = Step(
    name="deploy_backend",
    description="Deploys the backend service to the Kind cluster",
    perform=lambda **kwargs: deploy_backend(**kwargs),
    check=lambda **kwargs: check_backend_deployed(**kwargs),
    rollback=None,
    args={'cluster_name': KIND_CLUSTER_NAME},
    perform_flag="deploy_backend_only",
    step_kind=StepKind.Required(),
    depends_on=['build_and_push_images', 'create_gateway'],
)
