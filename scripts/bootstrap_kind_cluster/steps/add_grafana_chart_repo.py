import subprocess
from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind
from scripts.common.check_result import CheckPassed, CheckFailed, CheckResult
import scripts.common.helm as helm_module

def check_grafana_chart_repo_added() -> CheckResult:
    """Check that the 'grafana' Helm repository is present in the local cache."""
    try:
        result = subprocess.run(
            ["helm", "repo", "list", "--output", "json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        if result.returncode == 0 and '"grafana"' in result.stdout:
            return CheckPassed()
        return CheckFailed(errors=["Helm repository 'grafana' not found (run: helm repo add grafana https://grafana.github.io/helm-charts)"])
    except FileNotFoundError:
        return CheckFailed(errors=["helm not found"])

ADD_GRAFANA_CHART_REPO = Step(
    name="add_grafana_chart_repo",
    description="Adds the Grafana Helm chart repository",
    perform=lambda **kwargs: helm_module.add_grafana_helm_repo(),
    check=lambda **kwargs: check_grafana_chart_repo_added(),
    rollback=None,
    step_kind=StepKind.Required(),
    depends_on=['initialize_kind_cluster']
)
