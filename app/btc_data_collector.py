import time
import json
import asyncio
import requests
import threading
import websockets
from websocket import WebSocketApp
from collections import defaultdict

from polymarket.websocket_ob import polymarket_runner

from tools.writer import JSONLWriter
from tools.data_manager import DataManager
from binance.listeners.l2_listener import L2Listener
from binance.listeners.tape_listener import TapeListener
from binance.aggregators.l2_aggregator import L2Aggregator
from binance.aggregators.tape_aggregator import TapeAggregator

SYMBOL = "btcusdt"
DEPTH_WS = f"wss://stream.binance.com:9443/ws/{SYMBOL}@depth@100ms"
TAPE_WS = f"wss://stream.binance.com:9443/ws/{SYMBOL}@trade"

LEVELS_USED = 10
DATA_FOLDER = "data"

async def main():
    # event loop
    loop = asyncio.get_running_loop()

    # writers
    l2_writer = JSONLWriter(DATA_FOLDER, "l2.jsonl")
    tape_writer = JSONLWriter(DATA_FOLDER, "tape.jsonl")
    polymarket_writer = JSONLWriter(DATA_FOLDER, "polymarket.jsonl")
    data_manager_writer = JSONLWriter(DATA_FOLDER, "combined_data.jsonl")

    await asyncio.gather(
        # l2_writer.start(),
        # tape_writer.start(),
        # polymarket_writer.start(),
        data_manager_writer.start()
    )

    data_manager = DataManager(data_manager_writer)

    # listeners
    l2_listener = L2Listener(
        DEPTH_WS,
        LEVELS_USED,
        l2_writer,
        L2Aggregator(),
        data_manager
    )

    trade_listener = TapeListener(
        TAPE_WS,
        tape_writer,
        TapeAggregator(),
        data_manager
    )

    # polymarket runs in its own thread
    threading.Thread(
        target=polymarket_runner,
        args=(polymarket_writer, loop, data_manager),
        daemon=True
    ).start()

    # run everything
    await asyncio.gather(
        l2_listener.start_listening(),
        trade_listener.start_listening(),
    )


if __name__ == "__main__":
    asyncio.run(main())
    