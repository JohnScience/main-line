"""
Step class definitions for bootstrap_kind_cluster.

This module contains the core classes for defining and executing setup steps:
- StepKind: Defines whether a step is required or optional
- CliArg: Defines CLI arguments for steps
- Step: Represents a setup step with perform and rollback capabilities
- StepContext: Context manager for executing steps with automatic rollback- Output: Structured output from steps"""

from dataclasses import dataclass
from typing import Callable


@dataclass
class Output:
    """Structured output from a step execution."""
    title: str
    body: str


class StepKind:
    """Kind-specific data for steps, similar to PurposeSpecificDataVariant."""
    
    @dataclass
    class Required:
        """Step that always runs (unless explicitly skipped via perform_flag)."""
        pass
    
    @dataclass
    class Optional:
        """Step that only runs when explicitly requested or condition is met."""
        # The argument flag that, when set, skips this optional step
        # e.g., "skip_build" for --skip-build flag
        skip_flag: str | None = None
        # The argument flag that, when set, enables this optional step
        # e.g., "connect_kind" for --connect-kind flag
        enable_flag: str | None = None


StepKindData = StepKind.Required | StepKind.Optional


@dataclass
class CliArg:
    """Defines a CLI argument for a step."""
    name: str  # CLI arg name without dashes, e.g., "port" or "force_rebuild"
    arg_type: type = bool  # Argument type (bool, int, str, etc.)
    default: any = None  # Default value
    help: str = None  # General help text
    step_description: str = None  # Step-specific description for this argument
    
    def get_flag_name(self) -> str:
        """Convert name to CLI flag format: port -> --port"""
        return f'--{self.name.replace("_", "-")}'


@dataclass
class Step:
    """
    Represents a setup step with perform and rollback capabilities.
    """
    name: str
    description: str
    perform: Callable[..., bool | tuple[bool, list[Output]]]
    rollback: Callable[..., bool] | None = None
    completed: bool = False
    args: dict = None
    perform_flag: str = None  # e.g., "registry_only" for --registry-only
    rollback_flag: str = None  # e.g., "cleanup_registry" for --cleanup-registry
    step_kind: StepKindData = None  # Kind-specific data about how the step is controlled
    cli_arg_mappings: dict[str, str] = None  # Maps step arg names to CLI arg names
    cli_args: list[CliArg] = None  # CLI arguments this step uses
    
    def __post_init__(self):
        if self.args is None:
            self.args = {}
        if self.step_kind is None:
            self.step_kind = StepKind.Required()
        if self.cli_arg_mappings is None:
            self.cli_arg_mappings = {}
        if self.cli_args is None:
            self.cli_args = []
    
    def should_perform_only(self, parsed_args) -> bool:
        """Check if this step should run exclusively based on its perform flag."""
        if self.perform_flag:
            return getattr(parsed_args, self.perform_flag, False)
        return False
    
    def should_rollback(self, parsed_args) -> bool:
        """Check if this step should be rolled back based on its rollback flag."""
        if self.rollback_flag:
            return getattr(parsed_args, self.rollback_flag, False)
        return False
    
    def execute(self, step_num: int, total_steps: int) -> tuple[bool, list[Output]]:
        """
        Execute the step and track completion status.
        
        Args:
            step_num: Current step number (1-indexed)
            total_steps: Total number of steps
        
        Returns:
            tuple[bool, list[Output]]: Success status and list of outputs
        """
        print(f"\n[Step {step_num}/{total_steps}] {self.description}...")
        try:
            result = self.perform(**self.args)
            
            # Handle both old-style (bool) and new-style (tuple) returns
            if isinstance(result, tuple):
                success, outputs = result
            else:
                success = result
                outputs = []
            
            if success:
                self.completed = True
            return success, outputs
        except Exception as e:
            print(f"✗ Step failed with exception: {e}")
            return False, []
    
    def undo(self, force: bool = False) -> bool:
        """
        Rollback the step if it was completed.
        
        Args:
            force: If True, run rollback even if step wasn't completed
        
        Returns:
            bool: True if rollback successful or not needed, False otherwise
        """
        if not self.completed and not force:
            return True
        
        if self.rollback is None:
            print(f"  ℹ No rollback defined for step: {self.name}")
            return True
        
        print(f"  Rolling back step: {self.name}...")
        try:
            return self.rollback(**self.args)
        except Exception as e:
            print(f"  ✗ Rollback failed with exception: {e}")
            return False


class StepContext:
    """
    Context manager for executing steps with automatic rollback on failure.
    """
    def __init__(self, steps: list[Step], auto_rollback: bool = True):
        self.steps = steps
        self.auto_rollback = auto_rollback
        self.completed_steps: list[Step] = []
        self.all_outputs: list[Output] = []
    
    def execute_all(self) -> bool:
        """
        Execute all steps in order.
        
        Returns:
            bool: True if all steps succeeded, False otherwise
        """
        total_steps = len(self.steps)
        
        for i, step in enumerate(self.steps, start=1):
            success, outputs = step.execute(i, total_steps)
            
            # Collect outputs from this step
            self.all_outputs.extend(outputs)
            
            if success:
                self.completed_steps.append(step)
            else:
                print(f"\n✗ Step {i}/{total_steps} failed: {step.name}")
                
                if self.auto_rollback and self.completed_steps:
                    print("\n⚠ Rolling back completed steps...")
                    self.rollback_completed()
                
                return False
        
        return True
    
    def rollback_completed(self) -> bool:
        """
        Rollback all completed steps in reverse order.
        
        Returns:
            bool: True if all rollbacks succeeded, False otherwise
        """
        all_success = True
        
        for step in reversed(self.completed_steps):
            if not step.undo():
                all_success = False
        
        return all_success
