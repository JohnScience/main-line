import subprocess
from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind
from scripts.common.check_result import CheckPassed, CheckFailed, CheckResult
import scripts.common.helm as helm_module

def check_prometheus_community_chart_repo_added() -> CheckResult:
    """Check that the 'prometheus-community' Helm repository is present in the local cache."""
    try:
        result = subprocess.run(
            ["helm", "repo", "list", "--output", "json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        if result.returncode == 0 and '"prometheus-community"' in result.stdout:
            return CheckPassed()
        return CheckFailed(errors=["Helm repository 'prometheus-community' not found (run: helm repo add prometheus-community https://prometheus-community.github.io/helm-charts)"])
    except FileNotFoundError:
        return CheckFailed(errors=["helm not found"])

ADD_PROMETHEUS_COMMUNITY_CHART_REPO = Step(
    name="add_prometheus_community_chart_repo",
    description="Adds the Prometheus Community Helm chart repository",
    perform=lambda **kwargs: helm_module.add_prometheus_community_helm_repo(),
    check=lambda **kwargs: check_prometheus_community_chart_repo_added(),
    rollback=None,
    step_kind=StepKind.Required(),
    depends_on=['initialize_kind_cluster']
)
