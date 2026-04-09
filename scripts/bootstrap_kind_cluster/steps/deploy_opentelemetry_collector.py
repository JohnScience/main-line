import subprocess
import time
from pathlib import Path

from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind
from scripts.bootstrap_kind_cluster.check_result import CheckPassed, CheckFailed, CheckResult
from scripts.kind_cluster.index import KIND_CLUSTER_NAME
import scripts.common.kind as kind_module

project_root = Path(__file__).parent.parent.parent.parent


def wait_for_otel_operator() -> bool:
    try:
        subprocess.run(
            [
                "kubectl",
                "wait",
                "--for=condition=available",
                "deployment/opentelemetry-operator",
                "-n",
                "opentelemetry-operator",
                "--timeout=120s",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return True

    except subprocess.CalledProcessError as e:
        print("✗ OpenTelemetry Operator not ready")

        if e.stderr:
            print(e.stderr)

        return False


def wait_for_otel_webhook() -> bool:
    try:
        subprocess.run(
            [
                "kubectl",
                "wait",
                "--for=condition=Ready",
                "pod",
                "-l",
                "app.kubernetes.io/name=opentelemetry-operator",
                "-n",
                "opentelemetry-operator",
                "--timeout=120s",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def deploy_opentelemetry_collector() -> bool:
    """
    Deploy OpenTelemetry Collector in the Kind cluster for telemetry data collection.

    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\nDeploying OpenTelemetry Collector in Kind cluster '{KIND_CLUSTER_NAME}'...")
    if not kind_module.set_kubectl_context_for_kind_cluster(KIND_CLUSTER_NAME):
        print(f"✗ Failed to set kubectl context for Kind cluster '{KIND_CLUSTER_NAME}'")
        return False

    try:
        subprocess.run(
            ["kubectl", "create", "namespace", "opentelemetry-collector"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        # Ignore error if namespace already exists
        stderr = e.stderr.decode() if hasattr(e.stderr, 'decode') else str(e.stderr)
        if "AlreadyExists" in stderr:
            print("Namespace 'opentelemetry-collector' already exists. Continuing...")
        else:
            print(f"✗ Failed to create namespace for OpenTelemetry Collector: {e}")
            return False

    wait_for_otel_operator()

    # Retry waiting for webhook to be ready (up to 10 times, 5s interval)
    max_retries = 10
    for attempt in range(max_retries):
        if wait_for_otel_webhook():
            break
        print(f"Waiting for OpenTelemetry Operator webhook to be ready... (attempt {attempt+1}/{max_retries})")
        time.sleep(5)
    else:
        print("✗ OpenTelemetry Operator webhook is not ready after waiting.")
        return False

    # Retry logic for webhook race condition
    max_apply_retries = 5
    for apply_attempt in range(max_apply_retries):
        try:
            subprocess.run(
                ["kubectl", "apply", "-f", str(project_root / "k8s" / "opentelemetry-collector" / "OpenTelemetryCollector.yaml")],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            break  # Success
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode() if hasattr(e.stderr, 'decode') else str(e.stderr)
            # Check for webhook connection refused error
            if "failed calling webhook" in stderr and "connect: connection refused" in stderr:
                print(f"Webhook not ready (connection refused). Retrying in 5 seconds... (attempt {apply_attempt+1}/{max_apply_retries})")
                time.sleep(5)
                continue
            print("✗ Failed to deploy OpenTelemetry Collector")
            print("Command:", e.cmd)
            print("Exit code:", e.returncode)
            if e.stdout:
                print("\n--- STDOUT ---")
                print(e.stdout)
            if e.stderr:
                print("\n--- STDERR ---")
                print(e.stderr)
            return False
    else:
        print("✗ Failed to deploy OpenTelemetry Collector after multiple retries due to webhook connection issues.")
        return False

    print(f"✓ Successfully deployed OpenTelemetry Collector in Kind cluster '{KIND_CLUSTER_NAME}'")
    return True


def check_deploy_opentelemetry_collector(cluster_name: str = KIND_CLUSTER_NAME, **kwargs) -> CheckResult:
    if not kind_module.set_kubectl_context_for_kind_cluster(cluster_name, verbosity=0):
        return CheckFailed(errors=[f"Failed to set kubectl context for Kind cluster '{cluster_name}'"])
    try:
        result = subprocess.run(
            ["kubectl", "get", "opentelemetrycollector", "otel-collector", "-n", "opentelemetry-collector"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            return CheckPassed()
        return CheckFailed(errors=["OpenTelemetryCollector 'otel-collector' not found in namespace 'opentelemetry-collector'"])
    except FileNotFoundError:
        return CheckFailed(errors=["kubectl not found"])


DEPLOY_OPENTELEMETRY_COLLECTOR = Step(
    name="deploy_opentelemetry_collector",
    description="Deploys OpenTelemetry Collector in the Kind cluster",
    perform=lambda **kwargs: deploy_opentelemetry_collector(),
    check=lambda **kwargs: check_deploy_opentelemetry_collector(**kwargs),
    rollback=None,
    step_kind=StepKind.Required(),
    perform_flag="deploy_opentelemetry_collector_only",
    depends_on=['deploy_opentelemetry_operator'],
)
