from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind
import scripts.common.helm as helm_module

ADD_OPENTELEMETRY_CHART_REPO = Step(
    name="add_opentelemetry_chart_repo",
    description="Adds the OpenTelemetry Helm chart repository",
    perform=lambda **kwargs: helm_module.add_opentelemetry_helm_repo(),
    rollback=None,
    step_kind=StepKind.Required(),
    depends_on=['initialize_kind_cluster']
)
