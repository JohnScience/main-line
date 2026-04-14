import argparse
from dataclasses import dataclass
from typing import Callable

from scripts.common.check_result import CheckFailed, CheckPassed, CheckResult
from scripts.test_kind_cluster.general_tests import check_otlp_logs_received_by_loki, check_all_namespaces_exist, check_all_services_exist


@dataclass
class Test:
    name: str
    description: str
    test_func: Callable[..., CheckResult]


@dataclass
class TestableService:
    name: str
    description: str
    tests: list[Test]


ALL_TESTABLE_SERVICES: list[TestableService] = []

GENERAL_TESTS: list[Test] = [
    Test(
        name="all_namespaces_exist",
        description="Checks that every namespace defined in the Namespaces enum exists in the cluster and vice versa.",
        test_func=check_all_namespaces_exist,
    ),
    Test(
        name="all_services_exist",
        description="Checks that every service in KnownServices exists in its expected namespace.",
        test_func=check_all_services_exist,
    ),
    Test(
        name="otlp_logs_received_by_loki",
        description="Sends an OTLP log entry to the OTel Collector and verifies it is queryable in Loki.",
        test_func=check_otlp_logs_received_by_loki,
    ),
]


def _run_test(test: Test) -> bool:
    print(f"  [{test.name}] {test.description}")
    result = test.test_func()
    match result:
        case CheckPassed(warnings=warnings):
            print(f"    PASSED")
            for w in warnings:
                print(f"    WARNING: {w}")
            return True
        case CheckFailed(errors=errors):
            print(f"    FAILED")
            for e in errors:
                print(f"    ERROR: {e}")
            return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Kind cluster tests")
    parser.add_argument(
        "--service",
        metavar="SERVICE",
        help="Run tests only for the named service (omit to run all)",
    )
    args = parser.parse_args()

    passed = 0
    failed = 0

    # General tests
    if not args.service:
        print("\n=== General Tests ===")
        for test in GENERAL_TESTS:
            if _run_test(test):
                passed += 1
            else:
                failed += 1

    # Per-service tests
    services = ALL_TESTABLE_SERVICES
    if args.service:
        services = [s for s in ALL_TESTABLE_SERVICES if s.name == args.service]
        if not services:
            print(f"No service named '{args.service}' found.")

    for service in services:
        print(f"\n=== {service.name}: {service.description} ===")
        for test in service.tests:
            if _run_test(test):
                passed += 1
            else:
                failed += 1

    total = passed + failed
    print(f"\nResults: {passed}/{total} passed", "" if failed == 0 else f"({failed} failed)")

    if failed > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
