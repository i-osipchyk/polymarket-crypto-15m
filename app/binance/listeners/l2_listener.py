import json
import asyncio
import logging
import websockets
from collections import defaultdict

MAX_MESSAGE_SIZE = 2 * 1024 * 1024  # 2 MB
RECONNECT_DELAY = 5  # seconds


class L2Listener:
    def __init__(self, ws, levels_used, writer, aggregator, data_manager, logger=None):
        self.writer = writer
        self.ws = ws
        self.aggregator = aggregator
        self.levels_used = levels_used
        self.data_manager = data_manager
        self.bids = defaultdict(float)
        self.asks = defaultdict(float)
        self.logger = logger or logging.getLogger(__name__)

    async def start_listening(self):
        while True:
            try:
                async with websockets.connect(self.ws, max_size=MAX_MESSAGE_SIZE) as ws:
                    self.logger.info("L2Listener connected")
                    async for msg in ws:
                        try:
                            data = json.loads(msg)
                            ts = int(data["E"] / 1000)

                            for p, q in data["b"]:
                                p, q = float(p), float(q)
                                if q == 0:
                                    self.bids.pop(p, None)
                                else:
                                    self.bids[p] = q

                            for p, q in data["a"]:
                                p, q = float(p), float(q)
                                if q == 0:
                                    self.asks.pop(p, None)
                                else:
                                    self.asks[p] = q

                            top_bids = get_top_levels(self.bids, reverse=True, n=self.levels_used)
                            top_asks = get_top_levels(self.asks, reverse=False, n=self.levels_used)

                            metrics = self.aggregator.update_l2(top_bids, top_asks, ts)
                            if metrics:
                                await self.data_manager.get_l2_data(metrics)
                                await self.writer.write(metrics)

                        except (KeyError, TypeError, ValueError) as e:
                            self.logger.warning(f"L2Listener malformed message: {e}")

            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.logger.warning(f"L2Listener disconnected: {e}. Reconnecting in {RECONNECT_DELAY}s...")
                await asyncio.sleep(RECONNECT_DELAY)


def get_top_levels(book, reverse=False, n=10):
        levels = sorted(book.items(), key=lambda x: x[0], reverse=reverse)
        return [(p, q) for p, q in levels[:n] if q > 0]