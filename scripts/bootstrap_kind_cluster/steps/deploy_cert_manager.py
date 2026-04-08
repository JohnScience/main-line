from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind
import scripts.common.helm as helm_module

DEPLOY_CERT_MANAGER = Step(
    name="deploy_cert_manager",
    description="Deploys Cert-Manager in the Kind cluster",
    perform=lambda **kwargs: helm_module.deploy_cert_manager_via_helm(),
    perform_flag="deploy_cert_manager_only",
    rollback=None,
    step_kind=StepKind.Required(),
    depends_on=['initialize_kind_cluster'],
)
