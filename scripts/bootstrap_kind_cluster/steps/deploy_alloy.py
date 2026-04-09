import subprocess
from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind
from scripts.bootstrap_kind_cluster.check_result import CheckPassed, CheckFailed, CheckResult
import scripts.common.helm as helm_module
import scripts.common.kind as kind_module
from scripts.kind_cluster.index import KIND_CLUSTER_NAME

def check_alloy_deployed(cluster_name: str = KIND_CLUSTER_NAME, **kwargs) -> CheckResult:
    """Check that the Grafana Alloy DaemonSet exists in the grafana-alloy namespace."""
    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name, verbosity=0):
        return CheckFailed(errors=[f"Could not set kubectl context for cluster '{cluster_name}'"])
    try:
        result = subprocess.run(
            ["kubectl", "get", "daemonset", "grafana-alloy", "--namespace", "grafana-alloy"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            return CheckPassed()
        return CheckFailed(errors=["Alloy DaemonSet not found in namespace 'grafana-alloy'"])
    except FileNotFoundError:
        return CheckFailed(errors=["kubectl not found"])

DEPLOY_ALLOY = Step(
    name="deploy_alloy",
    description="Deploys Grafana Alloy in the Kind cluster",
    perform=lambda **kwargs: helm_module.deploy_alloy_via_helm(),
    check=lambda **kwargs: check_alloy_deployed(**kwargs),
    rollback=None,
    args={'cluster_name': KIND_CLUSTER_NAME},
    step_kind=StepKind.Required(),
    perform_flag="deploy_alloy_only",
    depends_on=['deploy_alloy_config']
)
