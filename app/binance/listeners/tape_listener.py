import json
import websockets


class TapeListener:
    def __init__(self, ws, writer, aggregator, data_manager):
        self.ws = ws
        self.writer = writer
        self.aggregator = aggregator
        self.data_manager = data_manager

    async def start_listening(self):
        async with websockets.connect(self.ws) as ws:
            async for msg in ws:
                data = json.loads(msg)

                price = float(data["p"])
                size = float(data["q"])
                side = "sell" if data["m"] else "buy"
                ts = int(data["T"] / 1000)

                metrics = self.aggregator.update_trade(price, size, side, ts)
                if metrics:
                    await self.data_manager.get_tape_data(metrics)
                    await self.writer.write(metrics)
