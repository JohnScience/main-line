from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind
from scripts.common.kubectl import create_namespace
from pathlib import Path
import subprocess

project_root = Path(__file__).parent.parent.parent.parent

def deploy_alloy_config(namespace="grafana-alloy") -> bool:
    print(f"Creating namespace '{namespace}' for Grafana Alloy...")
    if not create_namespace(namespace):
        print(f"✗ Failed to create namespace '{namespace}' (or kubectl not installed).")
        return False
    print(f"✓ Namespace '{namespace}' created or already exists.")

    print(f"Creating ConfigMap 'alloy-config' in namespace '{namespace}'...")
    try:
        subprocess.run(
            [
                "kubectl", "create", "configmap", "--namespace", namespace, "alloy-config",
                f"--from-file=config.alloy={project_root / 'k8s' / 'grafana-alloy' / 'config.alloy'}"
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"✓ ConfigMap 'alloy-config' created in namespace '{namespace}'.")
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode() if hasattr(e.stderr, 'decode') else str(e.stderr)
        if "AlreadyExists" in stderr:
            print(f"ℹ ConfigMap 'alloy-config' already exists in namespace '{namespace}'. Continuing...")
        else:
            print(f"✗ Failed to create ConfigMap 'alloy-config': {stderr}")
            return False
    return True

DEPLOY_ALLOY_CONFIG = Step(
    name="deploy_alloy_config",
    description="Deploys a ConfigMap for Grafana Alloy in Kind cluster",
    perform=lambda **kwargs: deploy_alloy_config(),
    rollback=None,
    step_kind=StepKind.Required(),
    perform_flag="deploy_alloy_config_only",
    depends_on=['initialize_kind_cluster', 'add_grafana_chart_repo']
)
