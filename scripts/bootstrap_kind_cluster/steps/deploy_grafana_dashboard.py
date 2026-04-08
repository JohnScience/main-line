import subprocess
import base64
import time

from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind, Output
from scripts.common.kubectl import create_namespace
import scripts.common.helm as helm_module


def deploy_grafana_dashboard(namespace="grafana-dashboard", secret_timeout=120) -> tuple[bool, list[Output]]:
    """
    Deploys the Grafana Dashboard and waits for the admin secret up to secret_timeout seconds.
    Prints diagnostics if the secret is not found in time.

    Args:
        namespace: Namespace to deploy Grafana Dashboard.
        secret_timeout: Maximum seconds to wait for the admin secret (default 300).

    Returns:
        tuple[bool, list[Output]]: Success status and list of outputs.
    """
    print(f"Deploying Grafana Dashboard in namespace '{namespace}'...")
    create_namespace(namespace)
    logical_chart_name = "main-line-grafana-dashboard"
    if not helm_module.deploy_grafana_dashboard_via_helm(namespace=namespace, logical_chart_name=logical_chart_name):
        print(f"✗ Failed to deploy Grafana Dashboard via Helm in namespace '{namespace}'")
        return False, []
    print(f"✓ Successfully deployed Grafana Dashboard in namespace '{namespace}'")

    admin_password = None
    poll_interval = 5
    waited = 0
    # Ensure a minimum timeout of 300 seconds (5 minutes)
    if secret_timeout < 300:
        secret_timeout = 300
    while waited < secret_timeout:
        try:
            result = subprocess.run(
                [
                    "kubectl", "get", "secret",
                    "--namespace", namespace,
                    logical_chart_name,
                    "-o", "jsonpath={.data.admin-password}"
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            admin_password_b64 = result.stdout.strip()
            if not admin_password_b64:
                print(f"✗ Grafana admin password not found in secret. The secret may not be ready yet.")
            else:
                try:
                    admin_password = base64.b64decode(admin_password_b64).decode("utf-8")
                except Exception as decode_err:
                    print(f"✗ Failed to decode Grafana admin password: {decode_err}")
                    admin_password = None
                break
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode() if hasattr(e.stderr, 'decode') else str(e.stderr)
            if "not found" in stderr or "Error from server" in stderr:
                if waited + poll_interval < secret_timeout:
                    print(f"Waiting for Grafana secret to be created... (waited {waited+poll_interval}/{secret_timeout} seconds)")
                    time.sleep(poll_interval)
                    waited += poll_interval
                    continue
                else:
                    print(f"✗ Grafana secret not found after waiting {secret_timeout} seconds. It may not have been created.")
                    print("\n--- Diagnostics: Grafana Pod Status ---")
                    try:
                        pod_status = subprocess.run([
                            "kubectl", "get", "pods", "-n", namespace
                        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                        print(pod_status.stdout)
                    except Exception as pod_err:
                        print(f"Failed to get pod status: {pod_err}")
                    print("\n--- Diagnostics: Helm Release Status ---")
                    try:
                        helm_status = subprocess.run([
                            "helm", "status", logical_chart_name, "-n", namespace
                        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                        print(helm_status.stdout)
                    except Exception as helm_err:
                        print(f"Failed to get Helm release status: {helm_err}")
            else:
                print(f"✗ Failed to retrieve Grafana admin password: {stderr}")
            admin_password = None
            break
        except Exception as e:
            print(f"✗ Unexpected error retrieving Grafana admin password: {e}")
            admin_password = None
            break

    if admin_password:
        print(f"\nGrafana admin password: {admin_password}\n")
        return True, [Output(title="Grafana Admin Password", body=admin_password)]
    else:
        print("\nCould not retrieve Grafana admin password.\n")
        return True, []


def shutdown_grafana_dashboard(namespace="grafana-dashboard") -> bool:
    """
    Uninstalls the Grafana dashboard Helm release and deletes its namespace.

    Args:
        namespace: The namespace where the Grafana dashboard is deployed.

    Returns:
        bool: True if successful, False otherwise.
    """
    print(f"Shutting down Grafana Dashboard in namespace '{namespace}'...")
    try:
        subprocess.run([
            "helm", "uninstall", "grafana-dashboard", "--namespace", namespace
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"✓ Uninstalled Grafana Dashboard Helm release in namespace '{namespace}'")
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode() if hasattr(e.stderr, 'decode') else str(e.stderr)
        if "not found" in stderr:
            print(f"ℹ Helm release 'grafana-dashboard' not found in namespace '{namespace}'. Continuing...")
        else:
            print(f"✗ Failed to uninstall Grafana Dashboard: {stderr}")
            return False
    try:
        subprocess.run([
            "kubectl", "delete", "namespace", namespace
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"✓ Deleted namespace '{namespace}'")
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode() if hasattr(e.stderr, 'decode') else str(e.stderr)
        if "not found" in stderr:
            print(f"ℹ Namespace '{namespace}' not found. Nothing to delete.")
        else:
            print(f"✗ Failed to delete namespace '{namespace}': {stderr}")
            return False
    return True


DEPLOY_GRAFANA_DASHBOARD = Step(
    name="deploy_grafana_dashboard",
    description="Deploys a pre-configured Grafana dashboard for Main-Line telemetry",
    perform=lambda **kwargs: deploy_grafana_dashboard(),
    rollback=None,
    step_kind=StepKind.Required(),
    perform_flag="deploy_grafana_dashboard_only",
    depends_on=['initialize_kind_cluster'],
)
