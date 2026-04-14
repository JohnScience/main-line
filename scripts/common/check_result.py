from dataclasses import dataclass, field

@dataclass
class CheckPassed:
    warnings: list[str] = field(default_factory=list)

@dataclass
class CheckFailed:
    errors: list[str]

CheckResult = CheckPassed | CheckFailed
