"""
Tests para reconcile_missed_results() sin conexión real.
"""
import pytest
from unittest.mock import MagicMock, patch

class TestReconciler:
    def test_reconcile_returns_empty_when_no_trade_journal(self):
        """Si no hay trade_journal, reconcile retorna dict vacío sin excepción."""
        from iqoptionapi.reconciler import Reconciler
        mock_api = MagicMock()
        # Sin trade_journal
        if hasattr(mock_api, 'trade_journal'):
            del mock_api.trade_journal
        
        reconciler = Reconciler(mock_api)
        result = reconciler.reconcile(since_ts=0.0)
        
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_reconcile_returns_unknown_when_betinfo_fails(self):
        """Si betinfo falla, el orden debe marcarse como 'unknown'."""
        from iqoptionapi.reconciler import Reconciler
        mock_api = MagicMock()
        mock_api.trade_journal.get_pending_since.return_value = {
            555: "binary"
        }
        mock_api.get_betinfo.return_value = (False, None)
        mock_api.api.position_history_event.wait.return_value = False
        
        reconciler = Reconciler(mock_api)
        result = reconciler.reconcile(since_ts=0.0)
        
        assert 555 in result
        assert result[555] == "unknown"
