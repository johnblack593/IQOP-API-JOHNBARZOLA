"""
iqoptionapi/async_api.py
─────────────────────────
Async wrapper for IQ_Option (stable_api).

Wraps every blocking method in asyncio.get_event_loop().run_in_executor()
so they can be awaited from async bot code without freezing the event loop.

Usage:
    api = AsyncIQ_Option("email", "password")
    connected, reason = await api.connect()
    success, order_id = await api.buy(10, "EURUSD", "call", 1)
    result = await api.check_win(order_id, timeout=60)
    await api.close()
"""
from __future__ import annotations

import asyncio
import functools
from concurrent.futures import ThreadPoolExecutor

from iqoptionapi.stable_api import IQ_Option
from iqoptionapi.core.logger import get_logger

logger = get_logger(__name__)


class AsyncIQ_Option:
    """
    Async façade over IQ_Option.

    All public methods are coroutines that delegate to the underlying
    synchronous IQ_Option instance running in a ThreadPoolExecutor.
    The executor is created on __init__ and shut down on close().

    Thread safety: each async call runs the sync method in a
    dedicated thread from the pool. The underlying IQ_Option methods
    already use threading.Event internally, so this is safe.
    """

    def __init__(
        self,
        email: str,
        password: str,
        account_type: str = "PRACTICE",
        max_workers: int = 4,
    ):
        """
        Args:
            email: IQ Option account email.
            password: IQ Option account password.
            account_type: "PRACTICE" or "REAL".
            max_workers: Size of the ThreadPoolExecutor.
                         4 is enough for sequential bots;
                         increase for concurrent signal engines.
        """
        self._sync = IQ_Option(email, password, account_type)
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="iqopt-worker",
        )
        self._loop: asyncio.AbstractEventLoop | None = None

    # ── INTERNAL HELPERS ──────────────────────────────────────────────

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Returns the running event loop, caching it after first call."""
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.get_event_loop()
        return self._loop

    async def _run(self, func, *args, **kwargs):
        """
        Runs a synchronous callable in the executor.
        Propagates asyncio.CancelledError cleanly.

        This is the ONLY place where sync→async bridging happens.
        Every public method must call this (no direct self._sync calls).
        """
        loop = self._get_loop()
        try:
            return await loop.run_in_executor(
                self._executor,
                functools.partial(func, *args, **kwargs),
            )
        except asyncio.CancelledError:
            logger.warning(
                "Async call cancelled: %s",
                getattr(func, "__name__", repr(func)),
            )
            raise

    # ── LIFECYCLE ─────────────────────────────────────────────────────

    async def connect(self, sms_code=None, ssid=None):
        """Connects to IQ Option. Returns (bool, reason)."""
        return await self._run(
            self._sync.connect, sms_code=sms_code, ssid=ssid
        )

    async def connect_2fa(self, sms_code: str):
        """Completes 2FA login. Returns (bool, reason)."""
        return await self._run(self._sync.connect_2fa, sms_code)

    async def close(self):
        """Gracefully closes connection and shuts down executor."""
        try:
            await self._run(self._sync.close)
        finally:
            self._executor.shutdown(wait=False)

    async def logout(self):
        return await self._run(self._sync.logout)

    # ── GRUPO A — OPCIONES ────────────────────────────────────────────
    # [BINARY / TURBO]

    async def buy(self, price, ACTIVES, ACTION, expirations):
        """Buy binary/turbo option. Returns (bool, order_id)."""
        return await self._run(
            self._sync.buy, price, ACTIVES, ACTION, expirations
        )

    async def buy_multi(self, price, ACTIVES, ACTION, expirations):
        """Buy multiple options simultaneously. Returns list[order_id]."""
        return await self._run(
            self._sync.buy_multi, price, ACTIVES, ACTION, expirations
        )

    async def buy_by_raw_expirations(
        self, price, active, direction, option, expired
    ):
        return await self._run(
            self._sync.buy_by_raw_expirations,
            price, active, direction, option, expired,
        )

    async def sell_option(self, options_ids):
        return await self._run(self._sync.sell_option, options_ids)

    async def check_win(self, id, timeout: float = 60):
        """Awaits binary/turbo result. Returns 'win'/'loose'/'equal'/None."""
        return await self._run(self._sync.check_win, id, timeout)

    async def check_win_v2(self, id, timeout: float = 60):
        return await self._run(self._sync.check_win_v2, id, timeout)

    async def check_win_v3(self, id):
        return await self._run(self._sync.check_win_v3, id)

    async def check_win_v4(self, id):
        return await self._run(self._sync.check_win_v4, id)

    async def get_betinfo(self, id):
        return await self._run(self._sync.get_betinfo, id)

    async def get_optioninfo(self, limit):
        return await self._run(self._sync.get_optioninfo, limit)

    async def get_optioninfo_v2(self, limit):
        return await self._run(self._sync.get_optioninfo_v2, limit)

    # [DIGITAL]

    async def buy_digital_spot(self, active, amount, action, duration):
        """Buy digital spot option. Returns (bool, order_id)."""
        return await self._run(
            self._sync.buy_digital_spot,
            active, amount, action, duration,
        )

    async def buy_digital_spot_v2(self, active, amount, action, duration):
        return await self._run(
            self._sync.buy_digital_spot_v2,
            active, amount, action, duration,
        )

    async def buy_digital(self, amount, instrument_id):
        return await self._run(
            self._sync.buy_digital, amount, instrument_id
        )

    async def sell_digital_option(self, order_id):
        return await self._run(
            self._sync.sell_digital_option, order_id
        )

    async def close_digital_option(self, position_id):
        return await self._run(
            self._sync.close_digital_option, position_id
        )

    async def check_win_digital(self, order_id, timeout: float = 60):
        return await self._run(
            self._sync.check_win_digital, order_id, timeout
        )

    async def check_win_digital_v2(self, order_id):
        return await self._run(
            self._sync.check_win_digital_v2, order_id
        )

    async def get_digital_payout(self, active, seconds: int = 0):
        return await self._run(
            self._sync.get_digital_payout, active, seconds
        )

    async def get_payout(self, active):
        return await self._run(self._sync.get_payout, active)

    async def get_digital_underlying_list_data(self):
        return await self._run(
            self._sync.get_digital_underlying_list_data
        )

    async def get_strike_list(self, ACTIVES, duration):
        return await self._run(
            self._sync.get_strike_list, ACTIVES, duration
        )

    # [BLITZ]

    async def buy_blitz(
        self, active, amount, action, current_price, duration: int = 5
    ):
        """Buy blitz option. Returns (bool, result)."""
        return await self._run(
            self._sync.buy_blitz,
            active, amount, action, current_price, duration,
        )

    # ── GRUPO B — MARGEN ──────────────────────────────────────────────
    # [ORDER LIFECYCLE]

    async def buy_order(
        self, instrument_type, instrument_id,
        side, amount, leverage,
        type="market", limit_price=None,
        stop_price=None, stop_lose_kind=None,
        stop_lose_value=None, take_profit_kind=None,
        take_profit_value=None, use_trail_stop=False,
        auto_margin_call=False,
        use_token_for_commission=False,
    ):
        """Place a margin/CFD order. Returns (bool, order_id)."""
        return await self._run(
            self._sync.buy_order,
            instrument_type=instrument_type,
            instrument_id=instrument_id,
            side=side, amount=amount, leverage=leverage,
            type=type, limit_price=limit_price,
            stop_price=stop_price,
            stop_lose_kind=stop_lose_kind,
            stop_lose_value=stop_lose_value,
            take_profit_kind=take_profit_kind,
            take_profit_value=take_profit_value,
            use_trail_stop=use_trail_stop,
            auto_margin_call=auto_margin_call,
            use_token_for_commission=use_token_for_commission,
        )

    async def open_margin_position(
        self, instrument_type, active_id,
        direction, amount, leverage,
        take_profit=None, stop_loss=None,
        timeout: float = 30.0,
    ):
        """Open modern margin position. Returns (bool, dict|str)."""
        return await self._run(
            self._sync.open_margin_position,
            instrument_type, active_id, direction,
            amount, leverage,
            take_profit=take_profit, stop_loss=stop_loss,
            timeout=timeout,
        )

    async def place_pending_order(
        self, active, instrument_type,
        side, amount, leverage,
        stop_price,
        take_profit=None, stop_loss=None,
    ):
        return await self._run(
            self._sync.place_pending_order,
            active, instrument_type, side, amount, leverage,
            stop_price,
            take_profit=take_profit, stop_loss=stop_loss,
        )

    async def cancel_pending_order(self, order_id):
        return await self._run(
            self._sync.cancel_pending_order, order_id
        )

    async def cancel_order(self, buy_order_id):
        return await self._run(
            self._sync.cancel_order, buy_order_id
        )

    async def change_order(
        self, ID_Name, order_id,
        stop_lose_kind, stop_lose_value,
        take_profit_kind, take_profit_value,
        use_trail_stop, auto_margin_call,
    ):
        return await self._run(
            self._sync.change_order,
            ID_Name, order_id,
            stop_lose_kind, stop_lose_value,
            take_profit_kind, take_profit_value,
            use_trail_stop, auto_margin_call,
        )

    async def modify_margin_tp_sl(
        self, order_id, take_profit=None, stop_loss=None
    ):
        return await self._run(
            self._sync.modify_margin_tp_sl, order_id,
            take_profit=take_profit, stop_loss=stop_loss,
        )

    async def change_auto_margin_call(
        self, ID_Name, ID, auto_margin_call
    ):
        return await self._run(
            self._sync.change_auto_margin_call,
            ID_Name, ID, auto_margin_call,
        )

    # [QUERY / STATUS]

    async def get_order(self, buy_order_id):
        return await self._run(self._sync.get_order, buy_order_id)

    async def get_async_order(self, buy_order_id):
        # get_async_order es puro lookup en memoria, NO bloquea.
        # Se expone async por uniformidad pero NO usa executor.
        return self._sync.get_async_order(buy_order_id)

    async def get_order_status(self, order_id, instrument_type):
        return await self._run(
            self._sync.get_order_status, order_id, instrument_type
        )

    async def get_pending(self, instrument_type):
        return await self._run(
            self._sync.get_pending, instrument_type
        )

    async def get_pending_orders(self, instrument_type):
        return await self._run(
            self._sync.get_pending_orders, instrument_type
        )

    async def check_binary_order(self, order_id):
        return await self._run(
            self._sync.check_binary_order, order_id
        )

    async def reconcile_missed_results(self, since_ts: float):
        return await self._run(
            self._sync.reconcile_missed_results, since_ts
        )

    # ── GRUPO C — DATOS DE MERCADO ────────────────────────────────────

    async def get_instruments(self, type: str):
        return await self._run(self._sync.get_instruments, type)

    async def get_blitz_instruments(self):
        return await self._run(self._sync.get_blitz_instruments)

    async def get_binary_option_detail(self):
        return await self._run(
            self._sync.get_binary_option_detail
        )

    async def get_all_profit(self):
        return await self._run(self._sync.get_all_profit)

    async def get_financial_information(self, activeId):
        return await self._run(
            self._sync.get_financial_information, activeId
        )

    async def get_marginal_balance(self, instrument_type):
        return await self._run(
            self._sync.get_marginal_balance, instrument_type
        )

    async def get_min_leverage(self, instrument_type, active_id):
        return await self._run(
            self._sync.get_min_leverage, instrument_type, active_id
        )

    async def get_leader_board(
        self, country, from_position,
        to_position, near_traders_count,
        user_country_id=0,
        near_traders_country_count=0,
        top_country_count=0,
        top_count=0, top_type=2,
    ):
        return await self._run(
            self._sync.get_leader_board,
            country, from_position, to_position,
            near_traders_count,
            user_country_id=user_country_id,
            near_traders_country_count=near_traders_country_count,
            top_country_count=top_country_count,
            top_count=top_count, top_type=top_type,
        )

    async def get_all_open_time(self):
        return await self._run(self._sync.get_all_open_time)

    async def get_candles(self, ACTIVE, size, count, endtime):
        return await self._run(
            self._sync.get_candles,
            ACTIVE, size, count, endtime,
        )

    # ── PASSTHROUGH DE PROPIEDADES DE SOLO LECTURA ────────────────────
    # Estas NO bloquean — acceso directo sin executor.

    @property
    def sync(self) -> IQ_Option:
        """Escape hatch: access the underlying sync API directly."""
        return self._sync

    def get_server_timestamp(self):
        """Non-blocking: reads cached value from timesync."""
        return self._sync.get_server_timestamp()

    def get_balance_id(self):
        return self._sync.get_balance_id()

    def get_all_ACTIVES_OPCODE(self):
        return self._sync.get_all_ACTIVES_OPCODE()

    def get_all_realtime_candles(self):
        return self._sync.get_all_realtime_candles()
