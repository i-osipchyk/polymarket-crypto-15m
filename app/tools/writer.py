import json
import asyncio
import os
import traceback
from datetime import datetime
from tools.tools import curr_timestamp_15min


class JSONLWriter:
    def __init__(self, base_dir: str, name: str, file_rotation: bool = True):
        """
        base_dir: e.g. 'data'
        name: e.g. 'polymarket.json' (will be formatted as MM_polymarket.jsonl)
        """
        self.base_dir = base_dir
        self.name = name

        self.queue = asyncio.Queue()
        self._task = None

        self._current_ts = None
        self._file = None

        self.file_rotation = file_rotation

    async def start(self):
        if self._task is None:
            self._task = asyncio.create_task(self._writer())

    async def write(self, obj):
        await self.queue.put(obj)

    def _open_new_file(self):
        """Rotate file if candle changed and create yyyy/mm/dd/hh/ structure"""
        candle_ts = curr_timestamp_15min()

        if candle_ts == self._current_ts:
            return

        # Close old file if it exists
        if self._file:
            self._file.close()

        # Convert timestamp to a datetime object
        # Note: Assuming curr_timestamp_15min() returns seconds. 
        # If it returns milliseconds, use candle_ts / 1000
        dt = datetime.fromtimestamp(candle_ts)

        # Create folder structure: base_dir/yyyy/mm/dd/hh
        dir_path = os.path.join(
            self.base_dir,
            dt.strftime('%Y'),
            dt.strftime('%m'),
            dt.strftime('%d'),
            dt.strftime('%H')
        )
        os.makedirs(dir_path, exist_ok=True)

        # Create filename: MM_filename.jsonl (e.g., 15_polymarket.jsonl)
        minute_prefix = dt.strftime('%M')
        file_name = f"{minute_prefix}_{self.name}"
        
        file_path = os.path.join(dir_path, file_name)
        
        # Open with line buffering (buffering=1) for real-time safety
        self._file = open(file_path, "a", encoding="utf-8", buffering=1)

        self._current_ts = candle_ts
        print(f"[JSONLWriter] Switched to {file_path}")

    async def _writer(self):
        try:
            while True:
                obj = await self.queue.get()

                if self.file_rotation:
                    self._open_new_file()
                
                # Ensure we have an open file before writing
                if self._file:
                    self._file.write(json.dumps(obj) + "\n")

                self.queue.task_done()

        except Exception:
            traceback.print_exc()
            raise
        