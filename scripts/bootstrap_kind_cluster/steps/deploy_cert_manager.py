import subprocess
from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind
from scripts.common.check_result import CheckPassed, CheckFailed, CheckResult
import scripts.common.helm as helm_module
import scripts.common.kind as kind_module
from scripts.kind_cluster.index import KIND_CLUSTER_NAME

def check_cert_manager_deployed(cluster_name: str = KIND_CLUSTER_NAME, **kwargs) -> CheckResult:
    """Check that the cert-manager deployment exists in the cert-manager namespace."""
    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name, verbosity=0):
        return CheckFailed(errors=[f"Could not set kubectl context for cluster '{cluster_name}'"])
    try:
        result = subprocess.run(
            ["kubectl", "get", "deployment", "cert-manager", "--namespace", "cert-manager"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            return CheckPassed()
        return CheckFailed(errors=["cert-manager deployment not found in namespace 'cert-manager'"])
    except FileNotFoundError:
        return CheckFailed(errors=["kubectl not found"])

DEPLOY_CERT_MANAGER = Step(
    name="deploy_cert_manager",
    description="Deploys Cert-Manager in the Kind cluster",
    perform=lambda **kwargs: helm_module.deploy_cert_manager_via_helm(),
    check=lambda **kwargs: check_cert_manager_deployed(**kwargs),
    perform_flag="deploy_cert_manager_only",
    rollback=None,
    args={'cluster_name': KIND_CLUSTER_NAME},
    step_kind=StepKind.Required(),
    depends_on=['initialize_kind_cluster'],
)
