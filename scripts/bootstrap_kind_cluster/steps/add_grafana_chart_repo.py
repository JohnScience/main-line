from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind
import scripts.common.helm as helm_module

ADD_GRAFANA_CHART_REPO = Step(
    name="add_grafana_chart_repo",
    description="Adds the Grafana Helm chart repository",
    perform=lambda **kwargs: helm_module.add_grafana_helm_repo(),
    rollback=None,
    step_kind=StepKind.Required(),
    depends_on=['initialize_kind_cluster']
)
