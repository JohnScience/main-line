from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind
import scripts.common.helm as helm_module

DEPLOY_OPENTELEMETRY_OPERATOR = Step(
    name="deploy_opentelemetry_operator",
    description="Deploys OpenTelemetry Operator in the Kind cluster",
    perform=lambda **kwargs: helm_module.deploy_opentelemetry_operator_via_helm(),
    rollback=None,
    step_kind=StepKind.Required(),
    perform_flag="deploy_opentelemetry_operator_only",
    depends_on=['initialize_kind_cluster', 'add_opentelemetry_chart_repo'],
)
