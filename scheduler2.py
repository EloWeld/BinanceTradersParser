import asyncio
import json
from datetime import datetime

from config import REFRESH_RATE, MSG

# ============= TIMER ============= #
from database import TracksDB
from main import get_nickanme, get_trader_positions, format_float, start_broadcast, os


async def process_info():
    import config
    print(f"******\t(POSTING ITERATION {config.get_posting_iteration()})\t******")
    curr_time = ':'.join(str(datetime.now().time()).split(':')[:2])
    post_time = os.environ["POSTING_TIME"]
    if curr_time == post_time:
        if not config.minute_msgs:
            config.minute_msgs = True
            for i in range(100):
                config.add_posting_iteration()

            print("******\t(Posting time! YO!)\t******")
            await start_broadcast()
    else:
        config.minute_msgs = False
        config.add_posting_iteration()


async def scheduled(interval, func):
    while True:
        await func()
        await asyncio.sleep(interval)


if __name__ == "__main__":
    asyncio.run(scheduled(27, process_info))
