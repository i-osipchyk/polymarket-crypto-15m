import json
import websockets
from collections import defaultdict


class L2Listener:
    def __init__(self, ws, levels_used, writer, aggregator, data_manager):
        self.writer = writer
        self.ws = ws
        self.aggregator = aggregator
        self.levels_used = levels_used
        self.data_manager = data_manager
        self.bids = defaultdict(float)
        self.asks = defaultdict(float)

    async def start_listening(self):
        async with websockets.connect(self.ws) as ws:
            async for msg in ws:
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

def get_top_levels(book, reverse=False, n=10):
        levels = sorted(book.items(), key=lambda x: x[0], reverse=reverse)
        return [(p, q) for p, q in levels[:n] if q > 0]