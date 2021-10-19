import asyncio
import json

from config import REFRESH_RATE, MSG

# ============= TIMER ============= #
from database import TracksDB
from main import get_nickanme, get_trader_positions, format_float


async def minute_timer():
    import main
    main.minute_msgs = False


async def parse():
    import config, main
    config.add_parsing_iteration()
    print(f'************** \t(ITERATION {config.get_parsing_iteration()}) \t***************')

    traders = TracksDB.get_traders()
    for trader in traders:
        print("Parsing trader:", json.loads(trader["data"])["trader_name"])
        # Get trader name
        trader_name = get_nickanme(trader)

        # Get trader positions from jsoned post request
        r_data = get_trader_positions(trader)
        if r_data:
            olddata = json.loads(trader["data"])
            jsdata = r_data["otherPositionRetList"]
            n_data = {
                "trader_name": trader_name,
                "len": len(jsdata),
                "pos": {d["symbol"]: d["amount"] for d in jsdata},
                "ent_prices": {d["symbol"]: d["entryPrice"] for d in jsdata},
            }
            # Update trader data in database
            TracksDB.update_trader_data(json.dumps(n_data), trader["id"])
            # print(jsdata, newdata)
            # Exit if trader has no positions else check equiality of data with
            # previous values
            if olddata != n_data:
                changes = []
                for nd in n_data["pos"].keys():
                    tiker = nd
                    chgName = 'Long' if n_data["pos"][nd] > 0 else 'Short'
                    ent_price = "%.3f" % n_data["ent_prices"][nd]
                    # Position opening
                    if "pos" not in olddata or nd not in olddata["pos"]:
                        changes.append(MSG["OPENED"].format(tiker, chgName, ent_price))
                    # Position diff calc
                    if "pos" not in olddata or (not isinstance(olddata["pos"], dict)):
                        print('Old data corrupted')
                    elif nd in olddata["pos"] and \
                            n_data["pos"][nd] != olddata["pos"][nd]:
                        diff = (n_data["pos"][nd] - olddata["pos"][nd]) / olddata["pos"][nd] * 100
                        emj = '🔼' if diff > 0 else '🔽'
                        diff = format_float(diff)
                        changes.append(MSG["CHANGE"].format(emj, tiker, chgName, diff, ent_price))
                # Position closing (if no olddata)
                try:
                    for od in olddata["pos"].keys():
                        chgName = 'Long' if olddata["pos"][od] > 0 else 'Short'
                        if od not in n_data["pos"]:
                            changes.append(MSG["CLOSED"].format(od, chgName))
                except:
                    pass
                if not changes:
                    continue
                print(changes)
                # Sending
                await main.bot.send_message(chat_id=main.os.environ["CHANNEL"],
                                            text=MSG["POST_TITLE"].format(trader_name, n_data["len"]) + '\n'.join(
                                                changes),
                                            parse_mode=main.ParseMode.HTML
                                            )
            else:
                print('No Changes')
            print('=' * 50)
    print('************** \t(ITERATION ENDED) \t***************')


async def scheduled(interval, func):
    while True:
        await func()
        await asyncio.sleep(interval)


if __name__ == "__main__":
    asyncio.run(scheduled(REFRESH_RATE, parse))
