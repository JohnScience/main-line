from argparse import Namespace
from dataclasses import dataclass

from scripts.bootstrap_kind_cluster.steps_base import Step, StepKind


@dataclass
class Cleanup:
    registry_port: int = 5000


@dataclass
class PerformSteps:
    steps: list[Step]
    auto_rollback: bool = True


@dataclass
class PerformChecks:
    steps: list[Step]


Handling = Cleanup | PerformSteps | PerformChecks


def args_to_handling(args: Namespace, all_steps: list[Step]) -> Handling:
    if args.cleanup:
        return Cleanup(registry_port=getattr(args, 'port', 5000))

    if args.checks:
        return PerformChecks(steps=list(all_steps))

    # Create step copies with CLI argument mappings applied
    steps: list[Step] = []
    for step_template in all_steps:
        step = Step(
            name=step_template.name,
            description=step_template.description,
            perform=step_template.perform,
            rollback=step_template.rollback,
            args=step_template.args.copy(),
            perform_flag=step_template.perform_flag,
            rollback_flag=step_template.rollback_flag,
            step_kind=step_template.step_kind,
            cli_arg_mappings=step_template.cli_arg_mappings,
            cli_args=step_template.cli_args,
        )
        for step_arg_name, cli_arg_name in step.cli_arg_mappings.items():
            if hasattr(args, cli_arg_name):
                step.args[step_arg_name] = getattr(args, cli_arg_name)
        steps.append(step)

    skip_steps = []
    if getattr(args, 'skip_steps', None):
        skip_steps = [s.strip() for s in args.skip_steps.split(',') if s.strip()]

    steps_to_run: list[Step] = []
    if getattr(args, 'steps', None):
        requested = [s.strip() for s in args.steps.split(',') if s.strip()]
        name_to_step = {step.name: step for step in steps}
        missing = [s for s in requested if s not in name_to_step]
        if missing:
            raise ValueError(f"Unknown step(s) in --steps: {', '.join(missing)}")
        steps_to_run = [name_to_step[s] for s in requested if s not in skip_steps]
    else:
        for step in steps:
            should_include = False
            if isinstance(step.step_kind, StepKind.Required):
                should_include = True
            elif isinstance(step.step_kind, StepKind.Optional):
                skip_flag = step.step_kind.skip_flag
                enable_flag = step.step_kind.enable_flag
                should_include = True
                if skip_flag and getattr(args, skip_flag, False):
                    should_include = False
                elif enable_flag and not getattr(args, enable_flag, False):
                    should_include = False
            if should_include and step.name not in skip_steps:
                steps_to_run.append(step)

    if getattr(args, 'until_step', None):
        until_index = next(
            (i for i, step in enumerate(steps_to_run) if step.name == args.until_step),
            None,
        )
        if until_index is not None:
            steps_to_run = steps_to_run[:until_index + 1]
        else:
            raise ValueError(f"Step '{args.until_step}' not found.")

    return PerformSteps(
        steps=steps_to_run,
        auto_rollback=not args.no_rollback,
    )