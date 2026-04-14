#!/usr/bin/env python3
"""
Main entry point for bootstrap_kind_cluster.

This module contains the main execution logic and step implementations
for bootstrapping a Kind cluster with a local Docker registry.
"""

import argparse
import sys
from pathlib import Path

from scripts.bootstrap_kind_cluster.args_handling import Cleanup, PerformChecks, PerformSteps, args_to_handling

from scripts.bootstrap_kind_cluster.steps.add_grafana_chart_repo import ADD_GRAFANA_CHART_REPO
from scripts.bootstrap_kind_cluster.steps.add_opentelemetry_chart_repo import ADD_OPENTELEMETRY_CHART_REPO
from scripts.bootstrap_kind_cluster.steps.add_prometheus_community_chart_repo import ADD_PROMETHEUS_COMMUNITY_CHART_REPO
from scripts.bootstrap_kind_cluster.steps.build_and_push_images import BUILD_AND_PUSH_IMAGES, cleanup_images
from scripts.bootstrap_kind_cluster.steps.connect_to_kind import CONNECT_TO_KIND
from scripts.bootstrap_kind_cluster.steps.create_gateway import CREATE_GATEWAY
from scripts.bootstrap_kind_cluster.steps.create_gatewayclass import CREATE_GATEWAYCLASS
from scripts.bootstrap_kind_cluster.steps.create_kubernetes_dashboard_admin import CREATE_KUBERNETES_DASHBOARD_ADMIN
from scripts.bootstrap_kind_cluster.steps.create_kubernetes_dashboard_httproute import CREATE_KUBERNETES_DASHBOARD_HTTPROUTE
from scripts.bootstrap_kind_cluster.steps.deploy_alloy import DEPLOY_ALLOY
from scripts.bootstrap_kind_cluster.steps.deploy_alloy_config import DEPLOY_ALLOY_CONFIG
from scripts.bootstrap_kind_cluster.steps.deploy_cert_manager import DEPLOY_CERT_MANAGER
from scripts.bootstrap_kind_cluster.steps.deploy_gateway_api_implementation import DEPLOY_GATEWAY_API_IMPLEMENTATION
from scripts.bootstrap_kind_cluster.steps.deploy_prometheus import DEPLOY_PROMETHEUS
from scripts.bootstrap_kind_cluster.steps.deploy_grafana_dashboard import DEPLOY_GRAFANA_DASHBOARD
from scripts.bootstrap_kind_cluster.steps.deploy_grafana_dashboard_direct_httproute import DEPLOY_GRAFANA_DASHBOARD_DIRECT_HTTPROUTE
from scripts.bootstrap_kind_cluster.steps.deploy_kubernetes_dashboard import DEPLOY_KUBERNETES_DASHBOARD
from scripts.bootstrap_kind_cluster.steps.deploy_loki import DEPLOY_LOKI
from scripts.bootstrap_kind_cluster.steps.deploy_opentelemetry_collector import DEPLOY_OPENTELEMETRY_COLLECTOR
from scripts.bootstrap_kind_cluster.steps.deploy_opentelemetry_operator import DEPLOY_OPENTELEMETRY_OPERATOR
from scripts.bootstrap_kind_cluster.steps.create_grafana_dashboard_httproute import CREATE_GRAFANA_DASHBOARD_HTTPROUTE
from scripts.bootstrap_kind_cluster.steps.initialize_kind_cluster import INITIALIZE_KIND_CLUSTER
from scripts.bootstrap_kind_cluster.steps.install_gateway_api_crds import INSTALL_GATEWAY_API_CRDS
from scripts.bootstrap_kind_cluster.steps.install_metallb import INSTALL_METALLB
from scripts.bootstrap_kind_cluster.steps.start_registry import START_REGISTRY, cleanup_registry

# Add project root to path to support both direct execution and module import
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.bootstrap_kind_cluster.steps_base import Step, StepContext, CliArg, Output

def cleanup_all(container_name: str = "main-line-registry", registry_host: str = "localhost", registry_port: int = 5000) -> bool:
    """
    Complete cleanup: remove registry container and all built images.
    
    Args:
        container_name: Name of the registry container
        registry_host: Registry hostname
        registry_port: Registry port number
    
    Returns:
        bool: True if all cleanup successful, False otherwise
    """
    print("=== Cleaning Up Bootstrap Setup ===")
    
    success = True
    
    # Clean up images first (while registry might still be running)
    if not cleanup_images(registry_host, registry_port):
        success = False
    
    # Then clean up registry
    if not cleanup_registry(container_name):
        success = False
    
    if success:
        print("\n✓ Cleanup complete!")
    else:
        print("\n⚠ Cleanup completed with some errors")
    
    return success



# Define all available steps
ALL_STEPS = [
    START_REGISTRY,
    BUILD_AND_PUSH_IMAGES,
    INITIALIZE_KIND_CLUSTER,
    CONNECT_TO_KIND,
    INSTALL_GATEWAY_API_CRDS,
    INSTALL_METALLB,
    DEPLOY_GATEWAY_API_IMPLEMENTATION,
    CREATE_GATEWAYCLASS,
    CREATE_GATEWAY,
    DEPLOY_KUBERNETES_DASHBOARD,
    CREATE_KUBERNETES_DASHBOARD_ADMIN,
    CREATE_KUBERNETES_DASHBOARD_HTTPROUTE,
    ADD_GRAFANA_CHART_REPO,
    ADD_PROMETHEUS_COMMUNITY_CHART_REPO,
    DEPLOY_PROMETHEUS,
    DEPLOY_LOKI,
    DEPLOY_ALLOY_CONFIG,
    DEPLOY_ALLOY,
    ADD_OPENTELEMETRY_CHART_REPO,
    DEPLOY_CERT_MANAGER,
    DEPLOY_OPENTELEMETRY_OPERATOR,
    DEPLOY_OPENTELEMETRY_COLLECTOR,
    DEPLOY_GRAFANA_DASHBOARD,
    CREATE_GRAFANA_DASHBOARD_HTTPROUTE,
    DEPLOY_GRAFANA_DASHBOARD_DIRECT_HTTPROUTE,
]

def make_description():
    description = 'Bootstrap a local Docker registry and Kind cluster for Main-Line development.'
    description += '\n\nAvailable Steps:'

    for step in ALL_STEPS:
        description += f'\n  - \'{step.name}\': {step.description}'
    
    return description

def add_basic_parser_arguments(parser: argparse.ArgumentParser):
    parser.add_argument(
        '--skip_steps',
        type=str,
        default=None,
        help='Comma-separated list of step names to skip (e.g. -skip_steps=build_and_push_images,deploy_kubernetes_dashboard)'
    )
    
    # Add global arguments
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Global argument. Performs complete cleanup'
    )
    parser.add_argument(
        '--no-rollback',
        action='store_true',
        help='Global argument. Disable automatic rollback on failure'
    )
    parser.add_argument(
        '--until-step',
        type=str,
        default=None,
        help="Run all steps up to and including the named step (e.g. --until-step=deploy_opentelemetry_collector)"
    )
    parser.add_argument(
        '--checks',
        action='store_true',
        help='Run checks instead of the main setup'
    )

def collect_added_args(steps: list[Step]) -> dict[str, list[dict[str, any]]]:
    """Collect all CLI arguments from steps and which steps use them.
    
    Args:
        steps: List of Step objects to analyze
    
    Returns:
        dict: Mapping of CLI flag name to list of usages (step and cli_arg info)
    """
    # Track which CLI args have been added and which steps use them
    # Format: {'--port': [{'step': step_obj, 'cli_arg': cli_arg_obj}, ...]}
    added_args = {}
    
    # First pass: collect all argument usages across steps
    for step in steps:
        for cli_arg in step.cli_args:
            flag_name = cli_arg.get_flag_name()
            if flag_name not in added_args:
                added_args[flag_name] = []
            added_args[flag_name].append({
                'step': step,
                'cli_arg': cli_arg
            })

    return added_args

def add_step_specific_parser_arguments(parser: argparse.ArgumentParser, added_args: dict[str, list[dict[str, any]]]):
    # Second pass: add arguments to parser with multi-line help
    for flag_name, usages in added_args.items():
        # Get the first usage for type and default info
        first_usage = usages[0]
        cli_arg = first_usage['cli_arg']
        
        # Build multi-line help text
        help_lines = [f"Step-specific argument. {cli_arg.help or f'{cli_arg.name} option'}"]
        
        if len(usages) > 1:
            help_lines[0] += f' [used in {len(usages)} steps]'
        else:
            help_lines[0] += f" [used in step '{usages[0]['step'].name}']"
        
        for usage in usages:
            step_name = usage['step'].name
            step_desc = usage['cli_arg'].step_description or 'used by this step'
            help_lines.append(f"  * In step '{step_name}': {step_desc}")
        
        help_text = '\n'.join(help_lines)
        
        # Add argument to parser
        if cli_arg.arg_type == bool:
            parser.add_argument(
                flag_name,
                action='store_true',
                help=help_text
            )
        else:
            parser.add_argument(
                flag_name,
                type=cli_arg.arg_type,
                default=cli_arg.default,
                help=help_text
            )

def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=make_description(),
        formatter_class=argparse.RawTextHelpFormatter
    )
    add_basic_parser_arguments(parser)
    added_args = collect_added_args(ALL_STEPS)    
    add_step_specific_parser_arguments(parser, added_args)
    # Add new --steps argument for comma-separated step names
    parser.add_argument(
        '--steps',
        type=str,
        default=None,
        help='Comma-separated list of step names to run (e.g. --steps=step1,step2)'
    )
    return parser

def main():
    """Main entry point for the script."""
    parser = make_parser()
    args = parser.parse_args()

    try:
        handling = args_to_handling(args, ALL_STEPS)
    except ValueError as e:
        print(str(e))
        return 1

    if isinstance(handling, Cleanup):
        return 0 if cleanup_all(registry_port=handling.registry_port) else 1

    if isinstance(handling, PerformChecks):
        from scripts.common.check_result import CheckPassed
        print("=== Running Checks ===")
        all_passed = True
        for step in handling.steps:
            if step.check is None:
                print(f"  ? {step.name}")
            else:
                result = step.check(**step.args)
                passed = isinstance(result, CheckPassed)
                status = "✓" if passed else "✗"
                print(f"  {status} {step.name}")
                if not passed:
                    for error in result.errors:
                        print(f"      {error}")
                    all_passed = False
        return 0 if all_passed else 1

    assert isinstance(handling, PerformSteps)

    print("=== Docker Registry and Kind Cluster Setup ===")

    context = StepContext(handling.steps, auto_rollback=handling.auto_rollback)
    success = context.execute_all()

    if not success:
        print("\n✗ Setup failed")
        return 1

    # Print all collected outputs
    if context.all_outputs:
        print("\n" + "=" * 60)
        print("Setup Complete - Important Information:")
        print("=" * 60)
        for output in context.all_outputs:
            print(f"\n{output.title}:")
            print(f"  {output.body}")
        print("\n" + "=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
