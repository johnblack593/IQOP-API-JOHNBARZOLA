"""Module for IQ option websocket."""

import json
import threading
import logging
from iqoptionapi.logger import get_logger
import websocket
from iqoptionapi.ws.received.technical_indicators import technical_indicators
from iqoptionapi.ws.received.time_sync import time_sync
from iqoptionapi.ws.received.heartbeat import heartbeat
from iqoptionapi.ws.received.balances import balances
from iqoptionapi.ws.received.profile import profile
from iqoptionapi.ws.received.balance_changed import balance_changed
from iqoptionapi.ws.received.candles import candles
from iqoptionapi.ws.received.buy_complete import buy_complete
from iqoptionapi.ws.received.option import option
from iqoptionapi.ws.received.position_history import position_history
from iqoptionapi.ws.received.list_info_data import list_info_data
from iqoptionapi.ws.received.candle_generated import candle_generated_realtime
from iqoptionapi.ws.received.candle_generated_v2 import candle_generated_v2
from iqoptionapi.ws.received.commission_changed import commission_changed
from iqoptionapi.ws.received.socket_option_opened import socket_option_opened
from iqoptionapi.ws.received.api_option_init_all_result import api_option_init_all_result
from iqoptionapi.ws.received.initialization_data import initialization_data
from iqoptionapi.ws.received.underlying_list import underlying_list
from iqoptionapi.ws.received.instruments import instruments
from iqoptionapi.ws.received.financial_information import financial_information
from iqoptionapi.ws.received.position_changed import position_changed
from iqoptionapi.ws.received.option_opened import option_opened
from iqoptionapi.ws.received.option_closed import option_closed
from iqoptionapi.ws.received.top_assets_updated import top_assets_updated
from iqoptionapi.ws.received.strike_list import strike_list
from iqoptionapi.ws.received.api_game_betinfo_result import api_game_betinfo_result
from iqoptionapi.ws.received.traders_mood_changed import traders_mood_changed
from iqoptionapi.ws.received.order import order
from iqoptionapi.ws.received.position import position
from iqoptionapi.ws.received.positions import positions
from iqoptionapi.ws.received.order_placed_temp import order_placed_temp
from iqoptionapi.ws.received.deferred_orders import deferred_orders
from iqoptionapi.ws.received.history_positions import history_positions
from iqoptionapi.ws.received.available_leverages import available_leverages
from iqoptionapi.ws.received.order_canceled import order_canceled
from iqoptionapi.ws.received.position_closed import position_closed
from iqoptionapi.ws.received.overnight_fee import overnight_fee
from iqoptionapi.ws.received.api_game_getoptions_result import api_game_getoptions_result
from iqoptionapi.ws.received.sold_options import sold_options
from iqoptionapi.ws.received.tpsl_changed import tpsl_changed
from iqoptionapi.ws.received.auto_margin_call_changed import auto_margin_call_changed
from iqoptionapi.ws.received.digital_option_placed import digital_option_placed
from iqoptionapi.ws.received.result import result
from iqoptionapi.ws.received.instrument_quotes_generated import instrument_quotes_generated
from iqoptionapi.ws.received.training_balance_reset import training_balance_reset
from iqoptionapi.ws.received.socket_option_closed import socket_option_closed
from iqoptionapi.ws.received.live_deal_binary_option_placed import live_deal_binary_option_placed
from iqoptionapi.ws.received.live_deal_digital_option import live_deal_digital_option
from iqoptionapi.ws.received.leaderboard_deals_client import leaderboard_deals_client
from iqoptionapi.ws.received.live_deal import live_deal
from iqoptionapi.ws.received.user_profile_client import user_profile_client
from iqoptionapi.ws.received.leaderboard_userinfo_deals_client import leaderboard_userinfo_deals_client
from iqoptionapi.ws.received.client_price_generated import client_price_generated
from iqoptionapi.ws.received.users_availability import users_availability



_MESSAGE_ROUTER: dict = {
    'api_game_betinfo_result': [api_game_betinfo_result],
    'api_game_getoptions_result': [api_game_getoptions_result],
    'api_option_init_all_result': [api_option_init_all_result],
    'auto-margin-call-changed': [auto_margin_call_changed],
    'available-leverages': [available_leverages],
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
    'financial-information': [financial_information],
    'heartbeat': [heartbeat],
    'history-positions': [history_positions],
    'initialization-data': [initialization_data],
    'instruments': [instruments],
    'instrument-quotes-generated': [instrument_quotes_generated],
    'leaderboard-deals-client': [leaderboard_deals_client],
    'leaderboard-userinfo-deals-client': [leaderboard_userinfo_deals_client],
    'listInfoData': [list_info_data],
    'live-deal': [live_deal],
    'live-deal-binary-option-placed': [live_deal_binary_option_placed],
    'live-deal-digital-option': [live_deal_digital_option],
    'option': [option],
    'option-closed': [option_closed],
    'option-opened': [option_opened],
    'order': [order],
    'order-canceled': [order_canceled],
    'order-placed-temp': [order_placed_temp], # order_placed_temp: called once — duplicate removed (audit SPRINT-02)
    'overnight-fee': [overnight_fee],
    'position': [position],
    'positions': [positions],
    'position-changed': [position_changed],
    'position-closed': [position_closed],
    'position-history': [position_history],
    'profile': [profile],
    'result': [result],
    'socket-option-closed': [socket_option_closed],
    'socket-option-opened': [socket_option_opened],
    'sold-options': [sold_options],
    'strike-list': [strike_list],
    'technical-indicators': [lambda api, msg: technical_indicators(api, msg, api.websocket_client.api_dict_clean)],
    'timeSync': [time_sync],
    'top-assets-updated': [top_assets_updated],
    'tpsl-changed': [tpsl_changed],
    'traders-mood-changed': [traders_mood_changed],
    'training-balance-reset': [training_balance_reset],
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
        with self.api._ws_lock:
            try:
                logger.debug("WS message received: %s chars", len(message))
                msg_name = None
                try:
                    parsed = json.loads(str(message))
                    msg_name = parsed.get("name")
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

    def on_close(self, wss, close_status_code, close_msg):  # pylint: disable=unused-argument
        """Method to process websocket close."""
        logger = get_logger(__name__)
        logger.debug("Websocket connection closed.")
        self.api.check_websocket_if_connect = 0
        
        # [KILL-SWITCH] Release all pending threading.Event objects on disconnect
        for attr in dir(self.api):
            if attr.endswith('_event') and hasattr(getattr(self.api, attr), 'set'):
                getattr(self.api, attr).set()
