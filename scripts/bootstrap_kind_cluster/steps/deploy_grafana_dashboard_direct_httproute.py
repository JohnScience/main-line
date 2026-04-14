import subprocess
from pathlib import Path

from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind, Output
from scripts.common.check_result import CheckPassed, CheckFailed, CheckResult
from scripts.kind_cluster.index import KIND_CLUSTER_NAME
import scripts.common.kind as kind_module

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


def check_deploy_grafana_dashboard_direct_httproute(cluster_name: str = KIND_CLUSTER_NAME, **kwargs) -> CheckResult:
    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name, verbosity=0):
        return CheckFailed(errors=[f"Failed to set kubectl context for Kind cluster '{cluster_name}'"])
    try:
        result = subprocess.run(
            ["kubectl", "get", "httproute", "grafana-dashboard-direct", "-n", "grafana-dashboard"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            return CheckPassed()
        return CheckFailed(errors=["HTTPRoute 'grafana-dashboard-direct' not found in namespace 'grafana-dashboard'"])
    except FileNotFoundError:
        return CheckFailed(errors=["kubectl not found"])


DEPLOY_GRAFANA_DASHBOARD_DIRECT_HTTPROUTE = Step(
    name="deploy_grafana_dashboard_direct_httproute",
    description="Deploys the direct HTTPRoute for Grafana Dashboard (grafana-dashboard-direct)",
    perform=lambda **kwargs: deploy_grafana_dashboard_direct_httproute(),
    check=lambda **kwargs: check_deploy_grafana_dashboard_direct_httproute(**kwargs),
    rollback=None,
    step_kind=StepKind.Required(),
    perform_flag="deploy_grafana_dashboard_direct_httproute_only",
    depends_on=['create_gateway', 'deploy_grafana_dashboard'],
)
