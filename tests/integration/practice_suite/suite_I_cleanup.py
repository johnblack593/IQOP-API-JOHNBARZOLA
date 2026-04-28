import time
from iqoptionapi.stable_api import IQ_Option
from tests.practice_suite.report import TestResult, ReportCollector

SUITE_NAME = "I_Cleanup"

def run(api: IQ_Option, collector: ReportCollector) -> None:
    # Test I-01: close() method exists
    start = time.time()
    try:
        assert hasattr(api, "close"), "IQ_Option missing close method"
        assert callable(api.close), "IQ_Option.close is not callable"
        collector.record(TestResult(SUITE_NAME, "I-01: close() method exists", "PASSED", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "I-01: close() method exists", "FAILED", detail=str(e), duration=time.time() - start))

    # Test I-02: Shared HTTP session is active before close
    start = time.time()
    try:
        from iqoptionapi.http.session import get_shared_session
        s = get_shared_session()
        assert s is not None, "Shared session is None before close"
        assert s.verify is not False, "Shared session verify is False"
        collector.record(TestResult(SUITE_NAME, "I-02: Session active prep", "PASSED", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "I-02: Session active prep", "FAILED", detail=str(e), duration=time.time() - start))

    # Test I-03: close() executes without exception
    start = time.time()
    try:
        api.close()
        collector.record(TestResult(SUITE_NAME, "I-03: close() execution", "PASSED", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "I-03: close() execution", "FAILED", detail=str(e), duration=time.time() - start))

    # Test I-04: HTTP session is None after close
    start = time.time()
    try:
        # Internally close() releases the singleton, so next get_shared_session should be a new one
        from iqoptionapi.http import session as session_module
        
        # After close_shared_session(), session_module._shared_session should be None
        assert session_module._shared_session is None, "Session internals did not become None"
        
        new_session = session_module.get_shared_session()
        assert new_session is not None, "get_shared_session failed to build a new session post-close"
        # Release the new session cleanly since we instantiated it
        session_module.close_shared_session()

        collector.record(TestResult(SUITE_NAME, "I-04: Session None post-close", "PASSED", duration=time.time() - start))
    except Exception as e:
        collector.record(TestResult(SUITE_NAME, "I-04: Session None post-close", "FAILED", detail=str(e), duration=time.time() - start))
