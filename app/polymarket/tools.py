import time
import json
import requests

from tools.tools import curr_timestamp_15min

def extract_asset_map(market_json):
    outcomes = json.loads(market_json["outcomes"])
    token_ids = json.loads(market_json["clobTokenIds"])

    assert len(outcomes) == len(token_ids)

    return {
        token_id: outcome.lower()
        for token_id, outcome in zip(token_ids, outcomes)
    }

def get_ids():
    curr_ts = curr_timestamp_15min()
    slug = f"btc-updown-15m-{curr_ts}"
    url = f"https://gamma-api.polymarket.com/markets/slug/{slug}"

    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    data = response.json()

    asset_id_maps = extract_asset_map(data)
    return asset_id_maps


def seconds_until_reconnect() -> int:
    now = time.time()
    interval = 15 * 60

    next_candle_start = now - (now % interval) + interval
    reconnect_time = next_candle_start

    return int(reconnect_time - now) + 1