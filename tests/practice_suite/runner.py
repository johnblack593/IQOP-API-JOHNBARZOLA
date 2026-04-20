import sys
from iqoptionapi.stable_api import IQ_Option
from tests.practice_suite import config
from tests.practice_suite.report import ReportCollector

from tests.practice_suite import suite_A_infrastructure
from tests.practice_suite import suite_B_account
from tests.practice_suite import suite_C_market_data
from tests.practice_suite import suite_D_candles
from tests.practice_suite import suite_E_binary_options
from tests.practice_suite import suite_F_digital_options
from tests.practice_suite import suite_G_cfd_orders
from tests.practice_suite import suite_H_reconnect
from tests.practice_suite import suite_I_cleanup
from tests.practice_suite import suite_J_blitz

def main():
    print("="*90)
    print(" IQOPTIONAPI PRACTICE INTEGRATION TEST SUITE RUNNER")
    print("="*90)

    critical_error = 0
    try:
        if not config.IQ_EMAIL or not config.IQ_PASSWORD:
            print("ERROR: Credentials missing. Aborting.")
            sys.exit(1)
            
        print(f"Connecting with email: {config.IQ_EMAIL}")
        api = IQ_Option(config.IQ_EMAIL, config.IQ_PASSWORD)
        config.api_instance = api
        
        check, msg = api.connect()
        if not check:
            print(f"ERROR: Connection failed => {msg}")
            sys.exit(1)
            
        # Ensure PRACTICE balance
        api.change_balance("PRACTICE")
        
        mode = "UNKNOWN"
        if hasattr(api, "get_balance_mode"):
            mode = api.get_balance_mode()
        elif hasattr(api, "get_balance_type"):
            mode = api.get_balance_type()
            
        print(f"Current mode: {mode}")
        if mode != "PRACTICE":
            print(f"CRITICAL: Failed to enforce PRACTICE account. Returned mode was {mode}. ABORTING.")
            api.close()
            sys.exit(1)

        collector = ReportCollector()
        
        suites = [
            suite_A_infrastructure,
            suite_B_account,
            suite_C_market_data,
            suite_D_candles,
            suite_E_binary_options,
            suite_F_digital_options,
            suite_G_cfd_orders,
            suite_H_reconnect,
            suite_J_blitz,
            suite_I_cleanup,
        ]
        
        print("\nExecuting suites...")
        for suite in suites:
            # After H_reconnect, config.api_instance may hold a new connection
            if config.api_instance is not None and config.api_instance is not api:
                api = config.api_instance
            suite.run(api, collector)
            
    except Exception as e:
        print(f"\nCRITICAL RUNTIME ERROR: {e}")
        critical_error = 1
        
    finally:
        # Guarantee teardown
        if config.api_instance:
            try:
                config.api_instance.close()
                print("\nGraceful api.close() successfully called in finally block.")
            except:
                pass
                
    if 'collector' in locals():
        # Prevent print_final from throwing sys.exit() directly inside finally
        print("\n" + "=" * 95)
        print(f"{'SUITE':<25} | {'TEST ID: Descripción':<32} | {'STATUS':<7} | {'ELAPSED':<8} | {'NOTES'}")
        print("-" * 95)
        
        for r in collector.results:
            status_text = f"{r.status:<7}"
            if sys.stdout.isatty():
                if r.status == "PASSED":
                    status_text = f"\033[92m{r.status:<7}\033[0m"
                elif r.status == "SKIPPED" or "SKIPPED" in r.status:
                    status_text = f"\033[93m{r.status:<7}\033[0m"
                else:
                    status_text = f"\033[91m{r.status:<7}\033[0m"
                
            detail = r.detail if r.detail else ""
            if len(detail) > 40:
                detail = detail[:37] + "..."
                
            print(f"{r.suite:<25} | {r.name:<32} | {status_text} | {r.duration:<8.2f} | {detail}")
        print("=" * 95)
        
        passed_count = sum(1 for r in collector.results if r.status == "PASSED")
        skipped_count = sum(1 for r in collector.results if r.status == "SKIPPED" or "SKIPPED" in r.status)
        failed_count = sum(1 for r in collector.results if r.status not in ("PASSED", "SKIPPED") and "SKIPPED" not in r.status)
        total_count = len(collector.results)
        
        print(f"PASSED:  {passed_count} / TOTAL: {total_count}")
        print(f"SKIPPED: {skipped_count}")
        print(f"FAILED:  {failed_count}")
        print(f"CRITICAL RUNTIME ERROR: {critical_error}")
        
        if failed_count > 0 or critical_error > 0:
            sys.exit(1)
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
