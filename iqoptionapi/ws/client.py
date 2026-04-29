"""Module for IQ option websocket."""

import json
import threading
import logging
from collections import defaultdict
from iqoptionapi.core.logger import get_logger
import websocket
from iqoptionapi.ws.received.market.technical_indicators import technical_indicators
from iqoptionapi.ws.received.auth.time_sync import time_sync
from iqoptionapi.ws.received.auth.heartbeat import heartbeat
from iqoptionapi.ws.received.auth.balance import balances
from iqoptionapi.ws.received.auth.profile import profile
from iqoptionapi.ws.received.auth.balance_changed import balance_changed
from iqoptionapi.ws.received.market.candles import candles
from iqoptionapi.ws.received.orders.buy_complete import buy_complete
from iqoptionapi.ws.received.positions.position_history import position_history
from iqoptionapi.ws.received.market.list_info_data import list_info_data
from iqoptionapi.ws.received.market.candle_generated import candle_generated_realtime
from iqoptionapi.ws.received.market.candle_generated_v2 import candle_generated_v2
from iqoptionapi.ws.received.market.commission_changed import commission_changed
from iqoptionapi.ws.received.orders.socket_option_opened import socket_option_opened
from iqoptionapi.ws.received.auth.api_option_init_all_result import api_option_init_all_result
from iqoptionapi.ws.received.auth.initialization_data import initialization_data
from iqoptionapi.ws.received.market.underlying_list import underlying_list
from iqoptionapi.ws.received.market.instruments import instruments
from iqoptionapi.ws.received.market.financial_information import financial_information
from iqoptionapi.ws.received.orders.option_opened import option_opened
from iqoptionapi.ws.received.market.top_assets_updated import top_assets_updated
from iqoptionapi.ws.received.market.strike_list import strike_list
from iqoptionapi.ws.received.orders.api_game_betinfo_result import api_game_betinfo_result
from iqoptionapi.ws.received.market.traders_mood_changed import traders_mood_changed
from iqoptionapi.ws.received.orders.order import OrderState
from iqoptionapi.ws.received.positions.position import position
from iqoptionapi.ws.received.positions.positions import positions
from iqoptionapi.ws.received.orders.order_placed_temp import order_placed_temp
from iqoptionapi.ws.received.orders.deferred_orders import deferred_orders
from iqoptionapi.ws.received.positions.history_positions import history_positions
from iqoptionapi.ws.received.market.available_leverages import available_leverages
from iqoptionapi.ws.received.orders.order_canceled import order_canceled
from iqoptionapi.ws.received.positions.position_closed import PositionClosed
from iqoptionapi.ws.received.positions.overnight_fee import OvernightFee
from iqoptionapi.ws.received.orders.api_game_getoptions_result import api_game_getoptions_result
from iqoptionapi.ws.received.orders.sold_options import sold_options
from iqoptionapi.ws.received.positions.tpsl_changed import tpsl_changed
from iqoptionapi.ws.received.positions.auto_margin_call_changed import auto_margin_call_changed
from iqoptionapi.ws.received.orders.digital_option_placed import digital_option_placed
from iqoptionapi.ws.received.market.digital_payout import digital_payout
from iqoptionapi.ws.received.auth.result import result
from iqoptionapi.ws.received.market.instrument_quotes_generated import instrument_quotes_generated
from iqoptionapi.ws.received.auth.training_balance_reset import training_balance_reset
from iqoptionapi.ws.received.orders.live_deal_binary_option_placed import live_deal_binary_option_placed
from iqoptionapi.ws.received.orders.live_deal_digital_option import live_deal_digital_option
from iqoptionapi.ws.received.market.leaderboard_deals_client import leaderboard_deals_client
from iqoptionapi.ws.received.market.live_deal import live_deal
from iqoptionapi.ws.received.auth.user_profile_client import user_profile_client
from iqoptionapi.ws.received.market.leaderboard_userinfo_deals_client import leaderboard_userinfo_deals_client
from iqoptionapi.ws.received.market.client_price_generated import client_price_generated
from iqoptionapi.ws.received.auth.users_availability import users_availability
from iqoptionapi.ws.received.positions.portfolio_get_positions import portfolio_get_positions
from iqoptionapi.ws.received.orders.margin_order_result import margin_order_result
from iqoptionapi.ws.received.positions.marginal_balance import MarginalBalance
from iqoptionapi.ws.received.orders.stop_order_placed import StopOrderPlaced
from iqoptionapi.ws.received.orders.order_changed import OrderChanged
from iqoptionapi.ws.received.auth.alerts import Alerts
from iqoptionapi.ws.received.market.short_active_info import ShortActiveInfo
from iqoptionapi.ws.received.market.exchange_rate import ExchangeRate
from iqoptionapi.ws.received.market.trading_params import TradingParams

# SPRINT 7: Reactive Event Handlers (Classes)
from iqoptionapi.ws.received.orders.option_closed import OptionClosed
from iqoptionapi.ws.received.positions.position_changed import PositionChanged
from iqoptionapi.ws.received.orders.socket_option_closed import SocketOptionClosed

# Instancias únicas para el router
_option_closed_handler = OptionClosed()
_position_changed_handler = PositionChanged()
_socket_option_closed_handler = SocketOptionClosed()
_stop_order_placed_handler = StopOrderPlaced()
_order_changed_handler = OrderChanged()
_marginal_balance_handler = MarginalBalance()
_order_state_handler = OrderState()
_position_closed_handler = PositionClosed()
_overnight_fee_handler = OvernightFee()
_alerts_handler = Alerts()
_short_active_info_handler = ShortActiveInfo()
_exchange_rate_handler = ExchangeRate()
_trading_params_handler = TradingParams()




_MESSAGE_ROUTER: dict = {
    'alerts': [_alerts_handler],
    'api_game_betinfo_result': [api_game_betinfo_result],
    'api_game_getoptions_result': [api_game_getoptions_result],
    'api_option_init_all_result': [api_option_init_all_result],
    'auto-margin-call-changed': [auto_margin_call_changed],
    'available-leverages': [available_leverages],
    'authenticated': [__import__('iqoptionapi.ws.received.auth.authenticated', fromlist=['authenticated']).authenticated],
    'balances': [balances],
    'balance-changed': [balance_changed],
    'buyComplete': [buy_complete],
    'candles': [candles],
    'candle-generated': [lambda api, msg: candle_generated_realtime(api, msg, api.websocket_client.dict_queue_add)],
    'candles-generated': [lambda api, msg: candle_generated_v2(api, msg, api.websocket_client.dict_queue_add)],
    'client-price-generated': [client_price_generated],
    'commission-changed': [commission_changed],
    'deferred-orders': [deferred_orders],
    'digital-option-placed': [lambda api, msg: digital_option_placed(api, msg, api.websocket_client.api_dict_clean)],
    'digital-payout': [digital_payout],
    'exchange-rate-generated': [_exchange_rate_handler],
    'financial-information': [financial_information],
    'heartbeat': [heartbeat],
    'history-positions': [history_positions],
    'initialization-data': [initialization_data],
    'instruments': [instruments],
    'instruments-list': [instruments],
    'instrument-quotes-generated': [instrument_quotes_generated],
    'leaderboard-deals-client': [leaderboard_deals_client],
    'leaderboard-userinfo-deals-client': [leaderboard_userinfo_deals_client],
    'listInfoData': [list_info_data],
    'live-deal': [live_deal],
    'live-deal-binary-option-placed': [live_deal_binary_option_placed],
    'live-deal-digital-option': [live_deal_digital_option],
    'option': [_option_closed_handler],
    'option-closed': [_option_closed_handler],
    'option-opened': [option_opened],

    'market-order-placed': [margin_order_result],
    'order': [_order_state_handler],
    'orders-state': [_order_state_handler],
    'order-changed': [_order_changed_handler],
    'order-canceled': [order_canceled],
    'order-placed-temp': [order_placed_temp],
    'stop-order-placed': [_stop_order_placed_handler],
    'marginal-balance': [_marginal_balance_handler],
    'overnight-fee': [_overnight_fee_handler],
    'portfolio.get-positions': [portfolio_get_positions],
    'position': [position],
    'positions': [positions],
    'positions-state': [positions],
    'position-changed': [_position_changed_handler],
    'position-closed': [_position_closed_handler],

    'position-history': [position_history],
    'short-active-info': [_short_active_info_handler],
    'profile': [profile],
    'result': [result],
    'socket-option-closed': [_socket_option_closed_handler],
    'socket-option-opened': [socket_option_opened],

    'sold-options': [sold_options],
    'strike-list': [strike_list],
    'technical-indicators': [lambda api, msg: technical_indicators(api, msg, api.websocket_client.api_dict_clean)],
    'timeSync': [time_sync],
    'top-assets-updated': [top_assets_updated],
    'tpsl-changed': [tpsl_changed],
    'traders-mood-changed': [traders_mood_changed],
    'training-balance-reset': [training_balance_reset],
    'trading-params': [_trading_params_handler],
    'underlying-list': [underlying_list],
    'users-availability': [users_availability],
    'user-profile-client': [user_profile_client]
}

class WebsocketClient(object):
    """Class for work with IQ option websocket."""

    def __init__(self, api):
        """
        :param api: The instance of :class:`IQOptionAPI
            <iqoptionapi.api.IQOptionAPI>`.
        """
        self.api = api
        self.dict_lock = threading.Lock()
        self.wss = websocket.WebSocketApp(
            self.api.wss_url, on_message=self.on_message,
            on_error=self.on_error, on_close=self.on_close,
            on_open=self.on_open)

    def dict_queue_add(self, dict, maxdict, key1, key2, key3, value):
        with getattr(self, 'dict_lock', __import__('contextlib').nullcontext()):
            if key3 in dict[key1][key2]:
                dict[key1][key2][key3] = value
            else:
                while True:
                    try:
                        dic_size = len(dict[key1][key2])
                    except Exception as e:
                        dic_size = 0
                    if dic_size < maxdict:
                        dict[key1][key2][key3] = value
                        break
                    else:
                        # del mini key
                        del dict[key1][key2][sorted(
                            dict[key1][key2].keys(), reverse=False)[0]]

    def api_dict_clean(self, obj):
        if len(obj) > 5000:
            for k in obj.keys():
                del obj[k]
                break

    def on_message(self, wss, message):  # pylint: disable=unused-argument
        """Method to process websocket messages."""
        logger = get_logger(__name__)
        # Sprint 4 TAREA 1: WS debug sequence capture
        if hasattr(self.api, '_log_ws_debug'):
            self.api._log_ws_debug(message)
        with self.api._ws_lock:
            try:
                logger.debug("WS message received: %s chars", len(message))
                msg_name = None
                try:
                    parsed = json.loads(str(message))
                    msg_name = parsed.get("name")
                    # S3-T2: Unwrap sendMessage envelope for modern protocol compatibility
                    if msg_name == "sendMessage" and isinstance(parsed.get("msg"), dict):
                        msg_name = parsed["msg"].get("name")
                except (json.JSONDecodeError, AttributeError):
                    logger.warning("Unparseable WS message received, skipping router dispatch")
                    parsed = None

                if msg_name and msg_name in _MESSAGE_ROUTER:
                    for handler in _MESSAGE_ROUTER[msg_name]:
                        try:
                            handler(self.api, parsed)
                        except Exception as e:
                            logger.error("Handler error for message '%s': %s", msg_name, e, exc_info=True)
                elif parsed is not None:
                    # Instrumentación temporal (T3 PASO A)
                    if parsed.get("microserviceName") or (msg_name and msg_name.startswith("option")):
                        logger.info("WS_RAW: name=%r micro=%r status=%r",
                            msg_name, parsed.get("microserviceName"),
                            parsed.get("msg", {}).get("status"))
                    logger.debug("No handler registered for message name: %s", msg_name)

            except Exception as e:
                logger.error("Critical error in on_message dispatch: %s", e, exc_info=True)

    def on_error(self, wss, error):  # pylint: disable=unused-argument
        """Method to process websocket errors."""
        logger = get_logger(__name__)
        logger.error(error)
        self.api.websocket_error_reason = str(error)
        self.api.check_websocket_if_error = True

    def on_open(self, wss):  # pylint: disable=unused-argument
        """Method to process websocket open."""
        logger = get_logger(__name__)
        logger.debug("Websocket client connected.")
        self.api.check_websocket_if_connect = 1
        self.api.ws_connected_event.set()

    def on_close(self, wss, close_status_code, close_msg):  # pylint: disable=unused-argument
        """Method to process websocket close."""
        logger = get_logger(__name__)
        logger.warning(
            "WS disconnected. Code=%s Msg=%s", close_status_code, close_msg
        )
        self.api.check_websocket_if_connect = 0
        self.api.ws_connected_event.clear()

        # KILL-SWITCH: liberar todos los _event y _store para desbloquear waits
        for attr in dir(self.api):
            if (attr.endswith('_event') or attr.endswith('_store')) and attr != 'ws_connected_event':
                ev = getattr(self.api, attr, None)
                if hasattr(ev, 'set'):
                    ev.set()
                elif isinstance(ev, (dict, defaultdict)):
                    # Liberar todos los eventos dentro del defaultdict/dict
                    for sub_ev in list(ev.values()):
                        if hasattr(sub_ev, 'set'):
                            sub_ev.set()

        # AUTO-RECONEXIÓN: lanzar en thread daemon para no bloquear on_close
        cb = getattr(self.api, '_reconnect_callback', None)
        if cb is not None and callable(cb):
            import threading
            t = threading.Thread(target=cb, daemon=True,
                                 name="AutoReconnect")
            t.start()
        else:
            logger.info("No reconnect callback registered — manual reconnect required.")

