import subprocess
from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind
from scripts.common.check_result import CheckPassed, CheckFailed, CheckResult
import scripts.common.helm as helm_module
import scripts.common.kind as kind_module
from scripts.kind_cluster.index import KIND_CLUSTER_NAME

def check_prometheus_deployed(cluster_name: str = KIND_CLUSTER_NAME, **kwargs) -> CheckResult:
    """Check that the Prometheus server deployment exists in the prometheus namespace."""
    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name, verbosity=0):
        return CheckFailed(errors=[f"Could not set kubectl context for cluster '{cluster_name}'"])
    try:
        result = subprocess.run(
            ["kubectl", "get", "deployment", "prometheus-server", "--namespace", "prometheus"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            return CheckPassed()
        return CheckFailed(errors=["Prometheus server deployment not found in namespace 'prometheus'"])
    except FileNotFoundError:
        return CheckFailed(errors=["kubectl not found"])

DEPLOY_PROMETHEUS = Step(
    name="deploy_prometheus",
    description="Deploys Prometheus in the Kind cluster",
    perform=lambda **kwargs: helm_module.deploy_prometheus_via_helm(),
    check=lambda **kwargs: check_prometheus_deployed(**kwargs),
    rollback=None,
    args={'cluster_name': KIND_CLUSTER_NAME},
    step_kind=StepKind.Required(),
    perform_flag="deploy_prometheus_only",
    depends_on=['initialize_kind_cluster', 'add_prometheus_community_chart_repo'],
)
