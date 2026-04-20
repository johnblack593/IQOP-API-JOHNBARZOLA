import sys
from iqoptionapi.stable_api import IQ_Option
from examples.practice_suite import config
from examples.practice_suite.report import ReportCollector

from examples.practice_suite import suite_A_infrastructure
from examples.practice_suite import suite_B_account
from examples.practice_suite import suite_C_market_data
from examples.practice_suite import suite_D_candles
from examples.practice_suite import suite_E_binary_options
from examples.practice_suite import suite_F_digital_options
from examples.practice_suite import suite_G_cfd_orders
from examples.practice_suite import suite_H_reconnect
from examples.practice_suite import suite_I_cleanup

def main():
    print("="*90)
    print(" IQOPTIONAPI PRACTICE INTEGRATION TEST SUITE RUNNER")
    print("="*90)

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
            suite_I_cleanup,
        ]
        
        print("\nExecuting suites...")
        for suite in suites:
            suite.run(api, collector)
            
        collector.print_final()

    except Exception as e:
        print(f"\nCRITICAL RUNTIME ERROR: {e}")
        # Make sure exit is non-zero
        sys.exit(1)
    finally:
        # Guarantee teardown
        if config.api_instance:
            try:
                config.api_instance.close()
                print("\nGraceful api.close() successfully called in finally block.")
            except:
                pass

if __name__ == "__main__":
    main()
