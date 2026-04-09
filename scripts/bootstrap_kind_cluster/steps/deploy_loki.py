import subprocess
from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind
from scripts.bootstrap_kind_cluster.check_result import CheckPassed, CheckFailed, CheckResult
import scripts.common.helm as helm_module
import scripts.common.kind as kind_module
from scripts.kind_cluster.index import KIND_CLUSTER_NAME

def check_loki_deployed(cluster_name: str = KIND_CLUSTER_NAME, **kwargs) -> CheckResult:
    """Check that the Loki StatefulSet exists in the loki namespace."""
    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name, verbosity=0):
        return CheckFailed(errors=[f"Could not set kubectl context for cluster '{cluster_name}'"])
    try:
        result = subprocess.run(
            ["kubectl", "get", "statefulset", "loki-backend", "--namespace", "loki"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            return CheckPassed()
        return CheckFailed(errors=["Loki StatefulSet not found in namespace 'loki'"])
    except FileNotFoundError:
        return CheckFailed(errors=["kubectl not found"])

DEPLOY_LOKI = Step(
    name="deploy_loki",
    description="Deploys Loki for log aggregation in the Kind cluster",
    perform=lambda **kwargs: helm_module.deploy_loki_via_helm(),
    check=lambda **kwargs: check_loki_deployed(**kwargs),
    rollback=None,
    args={'cluster_name': KIND_CLUSTER_NAME},
    step_kind=StepKind.Required(),
    perform_flag="deploy_loki_only",
    depends_on=['initialize_kind_cluster', 'add_grafana_chart_repo']
)
