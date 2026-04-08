from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind
import scripts.common.helm as helm_module

DEPLOY_LOKI = Step(
    name="deploy_loki",
    description="Deploys Loki for log aggregation in the Kind cluster",
    perform=lambda **kwargs: helm_module.deploy_loki_via_helm(),
    rollback=None,
    step_kind=StepKind.Required(),
    perform_flag="deploy_loki_only",
    depends_on=['initialize_kind_cluster', 'add_grafana_chart_repo']
)
