import asyncio
import json
from math import ceil

from aiogram import Bot, types, utils
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters import Text, CommandStart, Command
from aiogram.types import BotCommand, CallbackQuery, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
import requests
from aiogram.utils.markdown import text, underline, italic, bold

import nav
from config import *
from database import *
from filters import IsAdmin
from states import *
import bs4

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

minute_msgs = []


# ============= CALLBACKS ============= #
@dp.callback_query_handler(lambda c: "delete:" in c.data)
async def callbacks(cb: CallbackQuery):
    link = cb.data.split(':')[1]
    TracksDB.delete_trader(link)
    await cb.message.delete()


# ============= HANDLERS ============= #

@dp.message_handler(CommandStart())
async def cmdStart(message: types.Message):
    await message.answer(MSG["MOTO"], reply_markup=nav.main_menu)
    UsersDB.add_user(int(message.chat.id), message.from_user.username)


@dp.message_handler(Command('add_to_track'))
@dp.message_handler(Text('➕ Добавить ссылку на трек'))
async def btnAddToTrack(message: types.Message):
    if message.from_user.id in [x["tgid"] for x in UsersDB.all_admins()]:
        await message.answer("Оптравь ссылку на трек ✉")

        await MenuStates.Command.set()
    else:
        await message.answer("Сожалею, но вы не имеете прав на добавление треков")


def get_users_keyboard():
    users = UsersDB.all_users()
    max_rows = 3
    gps = ceil(len(users) / max_rows)
    print(gps)
    alls = []
    for i in range(gps):
        s = []
        for user in users[i * max_rows:(i + 1) * max_rows]:
            s.append(InlineKeyboardButton(
                text=f'{user["username"]} ({"🅰" if user["role"] == 1 else "😑"})',
                callback_data=f'user_role:{user["tgid"]}'
            ))
        alls.append(s)
    return InlineKeyboardMarkup(row_width=3, inline_keyboard=alls)


@dp.callback_query_handler(IsAdmin())
async def processCallbacks(cb: CallbackQuery):
    if 'user_role' in cb.data:
        user_tgid = cb.data.split(':')[1]
        print(UsersDB.get_role(user_tgid), user_tgid)
        new_role = 1 if UsersDB.get_role(user_tgid) == 0 else 0
        UsersDB.change_role(user_tgid, new_role)
        await cb.message.edit_reply_markup(get_users_keyboard())

        await bot.send_message(chat_id=user_tgid, text=MSG["GET_ROLE"].format(ROLES[new_role]))


@dp.message_handler(Command('users'), IsAdmin())
@dp.message_handler(Text('🤼‍♂️ Пользователи'), IsAdmin())
async def btnAddToTrack(message: types.Message):
    await message.answer(MSG["USERS"], reply_markup=get_users_keyboard())


@dp.message_handler(Command('all_tracks'))
@dp.message_handler(Text('📃 Трек'))
async def btnAllTrack(message: types.Message):
    tracks = TracksDB.get_traders()

    if not tracks:
        await message.answer('Треков нет')
        return
    else:
        await message.answer("Вот все треки")

        for tr in tracks:
            await message.answer(text=f'Id: {tr["id"]}\n'
                                      f'Link: {tr["link"]}\n'
                                      f'Position: {tr["pos"]}\n',
                                 reply_markup=nav.track_menu(tr["id"]))


@dp.message_handler(state=MenuStates.Command)
async def stateCommand(message: types.Message, state: FSMContext):
    # Filter
    if TRACK_COND in message.text:
        TracksDB.add_trader(message.text)

        await message.answer(MSG["TRACK_ADDED"])

    else:
        await message.answer(f'Некорректная ссылка! \nУсловие: {TRACK_COND}')

    await state.finish()


@dp.message_handler(Command('chatid '))
async def cmdAny(message: types.Message):
    print(message.chat.id)
    await message.answer(f'ChatID: {message.chat.id}')


# ============= PARSING ============= #
head = {
    'authority': 'www.binance.com',
    'content-type': 'application/json',
    'accept': '*/*',
}
session = requests.session()
session.headers.update(head)


def format_float(f, accuracy=ACCUR):
    return '+' + f"%.{accuracy}f" % f if f > 0 else f"%.{accuracy}f" % f


def get_nickanme(trader):
    encUid = trader["link"].split('encryptedUid=')[1]
    payload = {"encryptedUid": encUid}

    a = session.post(url=BINANCE_BASE_URL, data=json.dumps(payload), headers=head)
    if a.status_code != 200 or (not a.json()) or ("data" not in a.json()):
        return "Noname"
    return a.json()["data"]["nickName"]


def get_trader_positions(trader):
    encUid = trader["link"].split('encryptedUid=')[1]
    payload = {
        "encryptedUid": encUid, "tradeType": "PERPETUAL"
    }
    response = session.post(BINANCE_POS_URL, data=json.dumps(payload), headers=head)
    if (not response) or response.status_code != 20 or \
            (not response.json()) or \
            ("data" not in response.json()):
        return None
    return response.json()["data"]


def get_trader_performance(trader):
    encUid = trader["link"].split('encryptedUid=')[1]
    payload = {
        "encryptedUid": encUid,
        "tradeType": "PERPETUAL"
    }

    r = session.post(url=BINANCE_PERF_URL, data=json.dumps(payload), headers=head)
    if r.status_code != 200 or (not r.json()) or (not "data" in r.json()):
        return None
    roe_stat = {x["periodType"]: float(x["value"]) for x in r.json()["data"] if x["statisticsType"] == "ROI"}
    pnl_stat = {x["periodType"]: float(x["value"]) for x in r.json()["data"] if x["statisticsType"] == "PNL"}
    return roe_stat, pnl_stat


async def send_trader_info(trader, t_name: str):
    roe, pnl = get_trader_performance(trader)
    title = MSG["TRADER_INFO_TITLE"].format(t_name)
    description = ''
    for r in roe:
        description += f'<b>{str(r).capitalize().replace("_", " ")}</b>: {format_float(roe[r] * 100, 2)}% \n'

    footer = f"==============\n"

    for admin_id in [x["tgid"] for x in UsersDB.all_admins()]:
        await bot.send_message(chat_id=admin_id, text=title + description + footer, parse_mode=ParseMode.HTML)


async def process_info():
    global minute_msgs
    from datetime import datetime
    c_time = ':'.join(str(datetime.now().time()).split(':')[:2])
    print(c_time)
    if c_time != POSTING_TIME or len(minute_msgs) > 0:
        return
    minute_msgs += [1]
    traders = TracksDB.get_traders()
    for trader in traders:
        # Get trader name
        trader_name = get_nickanme(trader)
        # Check posting time
        await send_trader_info(trader, trader_name)


async def parse():
    traders = TracksDB.get_traders()
    for trader in traders:

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
            # print(jsdata, newdata)

            # Update trader data in database
            TracksDB.update_trader_data(json.dumps(n_data), trader["id"])
            # Exit if trader has no positions else check equiality of data with
            # previous values
            if (not isinstance(olddata["pos"], dict)) or "pos" not in olddata:
                return
            if olddata != n_data:
                changes = []
                for nd in n_data["pos"].keys():
                    tiker = nd
                    chgName = 'Long' if n_data["pos"][nd] > 0 else 'Short'
                    ent_price = "%.3f" % n_data["ent_prices"][nd]
                    # Position opening
                    if nd not in olddata["pos"]:
                        changes.append(MSG["OPENED"].format(tiker, chgName, ent_price))
                    # Position diff calc
                    if nd in olddata["pos"] and \
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
                    return
                print(changes)
                # Sending
                await bot.send_message(chat_id=CHAT_ID,
                                       text=MSG["POST_TITLE"].format(trader_name, n_data["len"]) + '\n'.join(changes),
                                       parse_mode=ParseMode.HTML
                                       )
                await bot.send_message(chat_id=CHANNAL_ID,
                                       text=MSG["POST_TITLE"].format(trader_name, n_data["len"]) + '\n'.join(changes),
                                       parse_mode=ParseMode.HTML
                                       )


# ============= TIMER ============= #

async def minute_timer():
    global minute_msgs
    minute_msgs = []


def timer_startup():
    loop_bot = asyncio.get_event_loop()
    loop_bot.create_task(scheduled(delay=0, interval=REFRESH_RATE, func=parse))
    loop_bot.create_task(scheduled(delay=0, interval=20, func=process_info))
    loop_bot.create_task(scheduled(delay=0, interval=60, func=minute_timer))


async def scheduled(delay, interval, func):
    await asyncio.sleep(delay)
    while True:
        await func()
        await asyncio.sleep(interval)


# ============= STARTUP ============= #
async def on_startup(dp):
    await set_default_commands(dp)


async def shutdown(dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        BotCommand("all_tracks", "Посмотреть трек"),
        BotCommand("add_to_track", "Добавить в трек линку"),
        BotCommand("users", "Список юзеров"),
    ])


if __name__ == "__main__":
    print("Binanser started")
    timer_startup()
    executor.start_polling(dp, on_startup=on_startup,
                           on_shutdown=shutdown)
