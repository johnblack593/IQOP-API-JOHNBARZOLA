import sys
from dataclasses import dataclass
from typing import List

@dataclass
class TestResult:
    suite:    str
    name:     str
    status:   str   # "PASSED", "FAILED", "SKIPPED"
    detail:   str = ""
    duration: float = 0.0   # seconds

class ReportCollector:
    def __init__(self):
        self.results: List[TestResult] = []

    def record(self, result: TestResult) -> None:
        # Backward compatibility for old signature if needed
        # Overwrite if detail signals skip
        if "SKIPPED" in result.detail and result.status == "PASSED":
            result.status = "SKIPPED"
            
        self.results.append(result)

    def print_final(self) -> None:
        print("\n" + "=" * 95)
        print(f"{'SUITE':<25} | {'TEST NAME':<32} | {'STATUS':<7} | {'DURATION':<8} | {'DETAIL'}")
        print("-" * 95)
        
        # ANSI colors for TTY
        COLOR_GREEN = '\033[92m'
        COLOR_YELLOW = '\033[93m'
        COLOR_RED = '\033[91m'
        COLOR_RESET = '\033[0m'
        
        for r in self.results:
            status_text = r.status
            if sys.stdout.isatty():
                if r.status == "PASSED":
                    status_text = f"{COLOR_GREEN}{r.status}{COLOR_RESET}"
                elif r.status == "SKIPPED" or "SKIPPED" in r.status:
                    status_text = f"{COLOR_YELLOW}{r.status}{COLOR_RESET}"
                else:
                    status_text = f"{COLOR_RED}{r.status}{COLOR_RESET}"
                
            detail = r.detail if r.detail else ""
            if len(detail) > 40:
                detail = detail[:37] + "..."
            
            # Print with exact width padding format despite ansi codes
            # The format string uses the uncolored string for padding to maintain alignment
            print(f"{r.suite:<25} | {r.name:<32} | {status_text:<7} | {r.duration:<8.2f} | {detail}")
        print("=" * 95)
        
        passed_count = sum(1 for r in self.results if r.status == "PASSED")
        skipped_count = sum(1 for r in self.results if r.status == "SKIPPED" or "SKIPPED" in r.status)
        failed_count = sum(1 for r in self.results if r.status not in ("PASSED", "SKIPPED") and "SKIPPED" not in r.status)
        total_count = len(self.results)
        
        print(f"PASSED:  {passed_count} / TOTAL: {total_count}")
        print(f"SKIPPED: {skipped_count}")
        print(f"FAILED:  {failed_count}")
        
        # runner.py is handling the critical runtime error 
        
        if failed_count > 0:
            sys.exit(1)
        # 0 means success
        # The runner.py wraps print_final, so if print_final sys.exits(), runner.py catches it in except Exception as e.
        sys.exit(0)
