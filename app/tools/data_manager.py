from tools.writer import JSONLWriter


class DataManager:
    def __init__(self, writer: JSONLWriter):
        self.data = {}
        self.writer = writer
        self.last_ts = None

    async def _check_and_flush(self, current_ts):
        """
        If we see a new timestamp, we assume the previous timestamp's 
        data is as complete as it's going to get.
        """
        if self.last_ts is not None and self.last_ts < current_ts:
            # Pop the completed record
            completed_record = self.data.pop(self.last_ts)
            # Add the timestamp back into the record for the file
            completed_record["timestamp"] = self.last_ts
            
            # Send to the async writer queue
            await self.writer.write(completed_record)
        
        self.last_ts = current_ts

    def get_pm_data(self, msg):
        ts = msg["ts"]

        if ts not in self.data:
            self.data[ts] = {}

        data = msg["data"]
        outcome = data.get("outcome")
        best_bid = data.get("best_bid")
        best_ask = data.get("best_ask")
        
        if outcome and best_bid and best_ask:
            self.data[ts].update({
                f"{outcome}_best_bid": best_bid,
                f"{outcome}_best_ask": best_ask
            })

    async def get_l2_data(self, metrics):
        ts = metrics.pop("ts")  # Correctly removes 'ts' and returns value
        await self._check_and_flush(ts)
        
        if ts not in self.data:
            self.data[ts] = {}
        self.data[ts].update(metrics) # Merges remaining keys

    async def get_tape_data(self, metrics):
        ts = metrics.pop("ts")
        await self._check_and_flush(ts)
        
        if ts not in self.data:
            self.data[ts] = {}
        self.data[ts].update(metrics)
        