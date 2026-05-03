"""
Unit tests for iqoptionapi/async_api.py — Async Bridge.

Uses unittest.mock.patch to bypass the real IQ_Option.__init__
and verify that every async wrapper correctly delegates to its
synchronous counterpart via _run().
"""
import asyncio
import inspect

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from iqoptionapi.async_api import AsyncIQ_Option


# ── Fixture ───────────────────────────────────────────────────────────

@pytest.fixture
def async_iq():
    """
    Creates an AsyncIQ_Option with a fully mocked _sync (IQ_Option).
    No real connection is made.
    """
    with patch("iqoptionapi.async_api.IQ_Option") as MockIQ:
        mock_sync = MagicMock()
        MockIQ.return_value = mock_sync
        api = AsyncIQ_Option("test@test.com", "pass123")
        # Sanity: _sync should be the mock
        assert api._sync is mock_sync
        yield api
        api._executor.shutdown(wait=False)


# ── Tests ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_connect_delegates_to_sync(async_iq):
    """await api.connect() calls sync.connect() exactly once."""
    async_iq._sync.connect.return_value = (True, None)
    result = await async_iq.connect()
    async_iq._sync.connect.assert_called_once()
    assert result == (True, None)


@pytest.mark.asyncio
async def test_buy_returns_tuple(async_iq):
    """sync.buy returns (True, 999); async returns same."""
    async_iq._sync.buy.return_value = (True, 999)
    result = await async_iq.buy(10, "EURUSD", "call", 1)
    async_iq._sync.buy.assert_called_once_with(10, "EURUSD", "call", 1)
    assert result == (True, 999)


@pytest.mark.asyncio
async def test_buy_digital_spot_returns_tuple(async_iq):
    async_iq._sync.buy_digital_spot.return_value = (True, 1234)
    result = await async_iq.buy_digital_spot("EURUSD", 5, "call", 1)
    async_iq._sync.buy_digital_spot.assert_called_once_with(
        "EURUSD", 5, "call", 1
    )
    assert result == (True, 1234)


@pytest.mark.asyncio
async def test_buy_order_passes_all_kwargs(async_iq):
    """buy_order passes ALL kwargs to the sync method."""
    async_iq._sync.buy_order.return_value = (True, "order_abc")
    result = await async_iq.buy_order(
        instrument_type="forex",
        instrument_id="EURUSD",
        side="buy",
        amount=100,
        leverage=50,
        type="market",
        limit_price=None,
        stop_price=None,
        stop_lose_kind="percent",
        stop_lose_value=50.0,
        take_profit_kind="percent",
        take_profit_value=100.0,
        use_trail_stop=True,
        auto_margin_call=False,
        use_token_for_commission=True,
    )
    async_iq._sync.buy_order.assert_called_once_with(
        instrument_type="forex",
        instrument_id="EURUSD",
        side="buy",
        amount=100,
        leverage=50,
        type="market",
        limit_price=None,
        stop_price=None,
        stop_lose_kind="percent",
        stop_lose_value=50.0,
        take_profit_kind="percent",
        take_profit_value=100.0,
        use_trail_stop=True,
        auto_margin_call=False,
        use_token_for_commission=True,
    )
    assert result == (True, "order_abc")


@pytest.mark.asyncio
async def test_buy_blitz_returns_tuple(async_iq):
    async_iq._sync.buy_blitz.return_value = (True, {"id": 42})
    result = await async_iq.buy_blitz("EURUSD", 1, "call", 1.23, 5)
    async_iq._sync.buy_blitz.assert_called_once_with(
        "EURUSD", 1, "call", 1.23, 5
    )
    assert result == (True, {"id": 42})


@pytest.mark.asyncio
async def test_open_margin_position_delegates(async_iq):
    async_iq._sync.open_margin_position.return_value = (True, {"id": "pos1"})
    result = await async_iq.open_margin_position(
        "forex", 1, "buy", 100, 50,
        take_profit=1.1, stop_loss=0.9, timeout=15.0,
    )
    async_iq._sync.open_margin_position.assert_called_once_with(
        "forex", 1, "buy", 100, 50,
        take_profit=1.1, stop_loss=0.9, timeout=15.0,
    )
    assert result == (True, {"id": "pos1"})


@pytest.mark.asyncio
async def test_cancel_order_returns_bool(async_iq):
    async_iq._sync.cancel_order.return_value = True
    result = await async_iq.cancel_order("order_123")
    async_iq._sync.cancel_order.assert_called_once_with("order_123")
    assert result is True


@pytest.mark.asyncio
async def test_change_order_delegates(async_iq):
    async_iq._sync.change_order.return_value = (True, {"status": 2000})
    result = await async_iq.change_order(
        "position_id", "ord1",
        "percent", 50.0,
        "percent", 100.0,
        False, True,
    )
    async_iq._sync.change_order.assert_called_once_with(
        "position_id", "ord1",
        "percent", 50.0,
        "percent", 100.0,
        False, True,
    )
    assert result == (True, {"status": 2000})


@pytest.mark.asyncio
async def test_get_order_delegates(async_iq):
    async_iq._sync.get_order.return_value = (True, {"id": 1})
    result = await async_iq.get_order("order_1")
    async_iq._sync.get_order.assert_called_once_with("order_1")
    assert result == (True, {"id": 1})


@pytest.mark.asyncio
async def test_get_async_order_no_executor(async_iq):
    """get_async_order does NOT use _run (it's a pure memory lookup)."""
    async_iq._sync.get_async_order.return_value = {"position-changed": {}}
    # Patch _run to detect if it gets called
    async_iq._run = AsyncMock(side_effect=AssertionError("_run should not be called"))
    result = await async_iq.get_async_order("order_x")
    async_iq._sync.get_async_order.assert_called_once_with("order_x")
    assert result == {"position-changed": {}}


@pytest.mark.asyncio
async def test_get_instruments_delegates(async_iq):
    async_iq._sync.get_instruments.return_value = {"instruments": []}
    result = await async_iq.get_instruments("forex")
    async_iq._sync.get_instruments.assert_called_once_with("forex")
    assert result == {"instruments": []}


@pytest.mark.asyncio
async def test_close_shuts_executor(async_iq):
    """After await api.close() the executor.shutdown was called."""
    async_iq._sync.close.return_value = None
    original_executor = async_iq._executor
    with patch.object(original_executor, "shutdown") as mock_shutdown:
        await async_iq.close()
        mock_shutdown.assert_called_once_with(wait=False)
    async_iq._sync.close.assert_called_once()


@pytest.mark.asyncio
async def test_cancelled_error_propagates(async_iq):
    """Simulates CancelledError in executor — must propagate up."""
    async_iq._sync.buy.side_effect = asyncio.CancelledError()
    with pytest.raises(asyncio.CancelledError):
        await async_iq.buy(1, "EURUSD", "call", 1)


@pytest.mark.asyncio
async def test_check_win_delegates_timeout(async_iq):
    """check_win(id, timeout=30) passes timeout=30 to sync."""
    async_iq._sync.check_win.return_value = "win"
    result = await async_iq.check_win("order_1", timeout=30)
    async_iq._sync.check_win.assert_called_once_with("order_1", 30)
    assert result == "win"


@pytest.mark.asyncio
async def test_check_win_digital_delegates(async_iq):
    async_iq._sync.check_win_digital.return_value = "loose"
    result = await async_iq.check_win_digital("dig_1", timeout=45)
    async_iq._sync.check_win_digital.assert_called_once_with("dig_1", 45)
    assert result == "loose"


@pytest.mark.asyncio
async def test_sell_option_delegates(async_iq):
    async_iq._sync.sell_option.return_value = True
    result = await async_iq.sell_option(["opt_1", "opt_2"])
    async_iq._sync.sell_option.assert_called_once_with(["opt_1", "opt_2"])
    assert result is True


@pytest.mark.asyncio
async def test_buy_multi_delegates(async_iq):
    async_iq._sync.buy_multi.return_value = [101, 102, None]
    result = await async_iq.buy_multi(5, "EURUSD", "call", 1)
    async_iq._sync.buy_multi.assert_called_once_with(5, "EURUSD", "call", 1)
    assert result == [101, 102, None]


@pytest.mark.asyncio
async def test_get_candles_delegates(async_iq):
    async_iq._sync.get_candles.return_value = [{"open": 1.1}]
    result = await async_iq.get_candles("EURUSD", 60, 100, 1600000000)
    async_iq._sync.get_candles.assert_called_once_with(
        "EURUSD", 60, 100, 1600000000
    )
    assert result == [{"open": 1.1}]


@pytest.mark.asyncio
async def test_get_all_open_time_delegates(async_iq):
    async_iq._sync.get_all_open_time.return_value = {"binary": {}}
    result = await async_iq.get_all_open_time()
    async_iq._sync.get_all_open_time.assert_called_once()
    assert result == {"binary": {}}


def test_passthrough_get_server_timestamp_no_await(async_iq):
    """get_server_timestamp() is NOT a coroutine — direct call."""
    async_iq._sync.get_server_timestamp.return_value = 1600000000
    result = async_iq.get_server_timestamp()
    assert result == 1600000000
    assert not inspect.iscoroutine(result)
    async_iq._sync.get_server_timestamp.assert_called_once()
