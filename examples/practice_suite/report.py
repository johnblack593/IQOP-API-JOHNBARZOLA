import sys
from dataclasses import dataclass
from typing import List

@dataclass
class TestResult:
    suite:    str
    name:     str
    passed:   bool
    detail:   str = ""
    duration: float = 0.0   # seconds

class ReportCollector:
    def __init__(self):
        self.results: List[TestResult] = []

    def record(self, result: TestResult) -> None:
        self.results.append(result)

    def print_final(self) -> None:
        print("\n" + "=" * 90)
        print(f"{'SUITE':<25} | {'TEST NAME':<30} | {'STATUS':<6} | {'DURATION':<8} | {'DETAIL'}")
        print("-" * 90)
        for r in self.results:
            status = "PASSED" if r.passed else "FAILED"
            detail = r.detail if r.detail else ""
            if len(detail) > 40:
                detail = detail[:37] + "..."
            print(f"{r.suite:<25} | {r.name:<30} | {status:<6} | {r.duration:<8.2f} | {detail}")
        print("=" * 90)
        
        passed_count = sum(1 for r in self.results if r.passed)
        total_count = len(self.results)
        print(f"PASSED: {passed_count} / TOTAL: {total_count}")
        
        if passed_count < total_count:
            sys.exit(1)
        sys.exit(0)
