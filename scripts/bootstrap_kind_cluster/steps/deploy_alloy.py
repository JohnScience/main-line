from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind
import scripts.common.helm as helm_module

DEPLOY_ALLOY = Step(
    name="deploy_alloy",
    description="Deploys Grafana Alloy in the Kind cluster",
    perform=lambda **kwargs: helm_module.deploy_alloy_via_helm(),
    rollback=None,
    step_kind=StepKind.Required(),
    perform_flag="deploy_alloy_only",
    depends_on=['deploy_alloy_config']
)
