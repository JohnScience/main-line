import subprocess
from pathlib import Path

from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind, Output
from scripts.kind_cluster.index import KIND_CLUSTER_NAME

project_root = Path(__file__).parent.parent.parent.parent


def deploy_grafana_dashboard_direct_httproute(
    cluster_name: str = KIND_CLUSTER_NAME,
    namespace: str = "grafana-dashboard",
) -> tuple[bool, list[Output]]:
    """
    Deploys the direct HTTPRoute for Grafana Dashboard from
    k8s/grafana-dashboard/httproute-direct.yaml.

    Returns:
        tuple[bool, list[Output]]: Success status and list of outputs
    """
    print(f"\nDeploying Grafana Dashboard direct HTTPRoute (grafana-dashboard-direct)...")
    try:
        httproute_path = project_root / "k8s" / "grafana-dashboard" / "httproute-direct.yaml"
        subprocess.run(
            ["kubectl", "apply", "-f", str(httproute_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(f"✓ Successfully deployed grafana-dashboard-direct HTTPRoute.")
        return True, [
            Output(
                title="Grafana Dashboard Direct HTTPRoute",
                body="Applied grafana-dashboard-direct HTTPRoute.",
            )
        ]
    except Exception as e:
        print(f"✗ Failed to deploy grafana-dashboard-direct HTTPRoute: {e}")
        return False, []


DEPLOY_GRAFANA_DASHBOARD_DIRECT_HTTPROUTE = Step(
    name="deploy_grafana_dashboard_direct_httproute",
    description="Deploys the direct HTTPRoute for Grafana Dashboard (grafana-dashboard-direct)",
    perform=lambda **kwargs: deploy_grafana_dashboard_direct_httproute(),
    rollback=None,
    step_kind=StepKind.Required(),
    perform_flag="deploy_grafana_dashboard_direct_httproute_only",
    depends_on=['create_gateway', 'deploy_grafana_dashboard'],
)
