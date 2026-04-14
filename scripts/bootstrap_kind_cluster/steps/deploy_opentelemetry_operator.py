import subprocess
from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind
from scripts.common.check_result import CheckPassed, CheckFailed, CheckResult
import scripts.common.helm as helm_module
import scripts.common.kind as kind_module
from scripts.kind_cluster.index import KIND_CLUSTER_NAME

def check_opentelemetry_operator_deployed(cluster_name: str = KIND_CLUSTER_NAME, **kwargs) -> CheckResult:
    """Check that the OpenTelemetry Operator deployment exists in the opentelemetry-operator namespace."""
    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name, verbosity=0):
        return CheckFailed(errors=[f"Could not set kubectl context for cluster '{cluster_name}'"])
    try:
        result = subprocess.run(
            ["kubectl", "get", "deployment", "opentelemetry-operator",
             "--namespace", "opentelemetry-operator"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            return CheckPassed()
        return CheckFailed(errors=["OpenTelemetry Operator deployment not found in namespace 'opentelemetry-operator'"])
    except FileNotFoundError:
        return CheckFailed(errors=["kubectl not found"])

DEPLOY_OPENTELEMETRY_OPERATOR = Step(
    name="deploy_opentelemetry_operator",
    description="Deploys OpenTelemetry Operator in the Kind cluster",
    perform=lambda **kwargs: helm_module.deploy_opentelemetry_operator_via_helm(),
    check=lambda **kwargs: check_opentelemetry_operator_deployed(**kwargs),
    rollback=None,
    args={'cluster_name': KIND_CLUSTER_NAME},
    step_kind=StepKind.Required(),
    perform_flag="deploy_opentelemetry_operator_only",
    depends_on=['initialize_kind_cluster', 'add_opentelemetry_chart_repo'],
)
