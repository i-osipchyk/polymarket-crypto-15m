import json
import asyncio
import logging
import websockets

MAX_MESSAGE_SIZE = 2 * 1024 * 1024  # 2 MB
RECONNECT_DELAY = 5  # seconds


class TapeListener:
    def __init__(self, ws, writer, aggregator, data_manager, logger=None):
        self.ws = ws
        self.writer = writer
        self.aggregator = aggregator
        self.data_manager = data_manager
        self.logger = logger or logging.getLogger(__name__)

    async def start_listening(self):
        while True:
            try:
                async with websockets.connect(self.ws, max_size=MAX_MESSAGE_SIZE) as ws:
                    self.logger.info("TapeListener connected")
                    async for msg in ws:
                        try:
                            data = json.loads(msg)

                            price = float(data["p"])
                            size = float(data["q"])
                            side = "sell" if data["m"] else "buy"
                            ts = int(data["T"] / 1000)

                            metrics = self.aggregator.update_trade(price, size, side, ts)
                            if metrics:
                                await self.data_manager.get_tape_data(metrics)
                                await self.writer.write(metrics)

                        except (KeyError, TypeError, ValueError) as e:
                            self.logger.warning(f"TapeListener malformed message: {e}")

            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.logger.warning(f"TapeListener disconnected: {e}. Reconnecting in {RECONNECT_DELAY}s...")
                await asyncio.sleep(RECONNECT_DELAY)
