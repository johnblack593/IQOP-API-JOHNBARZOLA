"""
Unit tests for Parquet export in TradeJournal.
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from iqoptionapi.trade_journal import TradeJournal, TradeRecord


def test_export_parquet_raises_importerror_without_pyarrow():
    """Verificar ImportError si pyarrow no está instalado."""
    # Mockear ImportError al importar pyarrow
    with patch.dict(sys.modules, {"pyarrow": None}):
        journal = TradeJournal(journal_dir="temp_journal")
        # Necesitamos al menos un trade para llegar al check de importación
        # (o el check está antes, en mi implementación está antes de get_trades_today)
        with pytest.raises(ImportError) as exc:
            journal.export_parquet()
        assert "pyarrow is required" in str(exc.value)


def test_export_parquet_raises_valueerror_on_empty_journal(tmp_path):
    """Con journal vacío -> ValueError."""
    # Aseguramos que pyarrow esté disponible para este test (o skipeamos)
    pytest.importorskip("pyarrow")
    
    journal = TradeJournal(journal_dir=str(tmp_path))
    with pytest.raises(ValueError) as exc:
        journal.export_parquet()
    assert "No trades recorded" in str(exc.value)


def test_export_parquet_creates_file(tmp_path):
    """Añadir 1 trade y verificar que se crea el archivo."""
    pytest.importorskip("pyarrow")
    
    journal = TradeJournal(journal_dir=str(tmp_path))
    # Mock de un record manual
    record = TradeRecord(
        trade_id="test-123",
        asset="EURUSD",
        direction="call",
        amount=10.0,
        duration_secs=60,
        asset_type="binary",
        strategy_id="test",
        signal_confidence=0.9,
        open_time="2026-05-03T00:00:00Z",
        session_id="sess-1"
    )
    journal._persist(record)
    
    parquet_path = str(tmp_path / "test.parquet")
    journal.export_parquet(filepath=parquet_path)
    
    assert os.path.exists(parquet_path)
    assert os.path.getsize(parquet_path) > 0


def test_export_parquet_returns_filepath(tmp_path):
    """El retorno del método debe ser la ruta absoluta del archivo."""
    pytest.importorskip("pyarrow")
    
    journal = TradeJournal(journal_dir=str(tmp_path))
    record = TradeRecord(
        trade_id="test-123", asset="EURUSD", direction="call", amount=10.0,
        duration_secs=60, asset_type="binary", strategy_id="test",
        signal_confidence=0.9, open_time="2026-05-03T00:00:00Z", session_id="sess-1"
    )
    journal._persist(record)
    
    parquet_path = str(tmp_path / "test.parquet")
    returned_path = journal.export_parquet(filepath=parquet_path)
    
    assert os.path.isabs(returned_path)
    assert returned_path.lower() == os.path.abspath(parquet_path).lower()


def test_export_parquet_schema_matches_csv_columns(tmp_path):
    """Verificar que el schema del Parquet coincide con las columnas esperadas."""
    pytest.importorskip("pyarrow")
    import pyarrow.parquet as pq
    
    journal = TradeJournal(journal_dir=str(tmp_path))
    record = TradeRecord(
        trade_id="test-123", asset="EURUSD", direction="call", amount=10.0,
        duration_secs=60, asset_type="binary", strategy_id="test",
        signal_confidence=0.9, open_time="2026-05-03T00:00:00Z", session_id="sess-1"
    )
    journal._persist(record)
    
    parquet_path = str(tmp_path / "test.parquet")
    journal.export_parquet(filepath=parquet_path)
    
    table = pq.read_table(parquet_path)
    parquet_columns = table.column_names
    
    expected_columns = [
        "trade_id", "asset", "direction", "amount", "duration_secs",
        "asset_type", "strategy_id", "signal_confidence", "open_time",
        "close_time", "open_price", "close_price", "result", "profit_usd",
        "metadata", "session_id"
    ]
    
    assert set(parquet_columns) == set(expected_columns)


def test_export_parquet_default_path_uses_journal_dir(tmp_path):
    """Verificar que el archivo se crea en journal_dir si filepath es None."""
    pytest.importorskip("pyarrow")
    
    journal = TradeJournal(journal_dir=str(tmp_path))
    record = TradeRecord(
        trade_id="test-123", asset="EURUSD", direction="call", amount=10.0,
        duration_secs=60, asset_type="binary", strategy_id="test",
        signal_confidence=0.9, open_time="2026-05-03T00:00:00Z", session_id="sess-1"
    )
    journal._persist(record)
    
    returned_path = journal.export_parquet()
    
    assert os.path.dirname(returned_path).lower() == str(tmp_path).lower()
    assert returned_path.endswith(".parquet")
    assert os.path.exists(returned_path)
