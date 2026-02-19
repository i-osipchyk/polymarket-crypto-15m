import json
import time
import asyncio
import requests
import threading
from websocket import WebSocketApp

from polymarket.tools import get_ids, seconds_until_reconnect


class WebSocketOrderBook:
    def __init__(self, channel_type, url, asset_id_maps, writer, loop, data_manager, logger):
        self.channel_type = channel_type
        self.url = url
        self.asset_id_maps = asset_id_maps
        self.writer = writer
        self.loop = loop
        self.data_manager = data_manager
        self.logger = logger

        furl = url + "/ws/" + channel_type
        self.ws = WebSocketApp(
            furl,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
        )
        self._stop_event = threading.Event()

    def on_message(self, ws, message):
        try:
            if message == "PONG":
                return
            msg = json.loads(message)
            if isinstance(msg, dict) and "event_type" in msg:
                if msg.get("event_type") == "best_bid_ask":
                    msg["outcome"] = self.asset_id_maps.get(msg["asset_id"], "unknown")
                    metrics = {
                        "ts": int(time.time()),
                        "source": "polymarket",
                        "data": msg
                    }

                    self.data_manager.get_pm_data(metrics)
                        
                    asyncio.run_coroutine_threadsafe(
                        self.writer.write(metrics),
                        self.loop
                    )

        except Exception as e:
            self.logger.error(f"Polymarket error: {e} on message {message}")


    def on_error(self, ws, error):
        self.logger.error(f"Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        self.logger.info(f"Polymarket closing: {close_status_code}, {close_msg}")

    def on_open(self, ws):
        ws.send(json.dumps({
            "type": self.channel_type,
            "assets_ids": list(self.asset_id_maps.keys()),
            "custom_feature_enabled": True
        }))

        threading.Thread(target=self.ping, args=(ws,), daemon=True).start()

    def ping(self, ws):
        while not self._stop_event.is_set():
            try:
                ws.send("PING")
                time.sleep(10)
            except Exception:
                break

    def run(self):
        while not self._stop_event.is_set():
            self.logger.info("Starting WebSocket connection...")
            self.ws.run_forever(ping_interval=30, ping_timeout=10)
            
            if not self._stop_event.is_set():
                self.logger.warning("WebSocket disconnected unexpectedly. Retrying in 5s...")
                time.sleep(5)

    def connect(self):
        self._stop_event.clear()
        self.ws.run_forever(
            ping_interval=30, 
            ping_timeout=10, 
            reconnect=5
        )

    def disconnect(self):
        self._stop_event.set()
        try:
            self.ws.close()
        except Exception:
            pass


def polymarket_runner(writer, loop, data_manager, logger):
    url = "wss://ws-subscriptions-clob.polymarket.com"

    while True:
        try:
            asset_id_maps = get_ids()
            logger.info(f"Polymarket IDs: {asset_id_maps}")

            market_connection = WebSocketOrderBook(
                "market", url, asset_id_maps, writer, loop, data_manager, logger
            )

            t = threading.Thread(
                target=market_connection.connect,
                daemon=True
            )
            t.start()

            sleep_s = seconds_until_reconnect()
            logger.info(f"[Polymarket] sleeping {sleep_s}s")
            time.sleep(sleep_s)

            logger.info("[Polymarket] reconnecting")
            market_connection.disconnect()
            time.sleep(1)

        except Exception as e:
            logger.error(f"[Polymarket] error: {e}")
            time.sleep(5)
