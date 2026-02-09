import time


def curr_timestamp_15min() -> int:
    now = int(time.time())
    interval = 15 * 60
    return now - (now % interval)