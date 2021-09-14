import asyncio
import json

from aiogram import Bot, types, utils
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters import Text, CommandStart, Command
from aiogram.types import BotCommand, CallbackQuery
from aiogram.utils import executor
import requests

import nav
from config import *
from database import *
from states import *
import bs4

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

TracksDB = TracksDatabase()
UsersDB = UsersDatabase()


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

        await message.answer("Ок, добавил")

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


def format_float(f):
    return '+' + f"%.{ACCUR}f" % f if f > 0 else f"%.{ACCUR}f" % f


def get_nickanme(uid: str):
    url = 'https://www.binance.com/bapi/futures/v2/public/future/leaderboard/getOtherLeaderboardBaseInfo'
    payload = {
        "encryptedUid": uid
    }
    head = {
        'authority': 'www.binance.com',
        'content-type': 'application/json',
        'accept': '*/*',
    }

    a = session.post(url=url, data=json.dumps(payload), headers=head)
    if a.status_code != 200:
        return "Noname"
    return a.json()["data"]["nickName"]


async def parse():
    traders = TracksDB.get_traders()
    for trader in traders:
        encUid = trader["link"].split('encryptedUid=')[1]
        payload = {
            "encryptedUid": encUid, "tradeType": "PERPETUAL"
        }
        response = session.post(BINANCE_API_URL, data=json.dumps(payload), headers=head)

        trader_name = get_nickanme(encUid)
        if response and response.json() and response.json()["data"]:
            jsdata = response.json()["data"]["otherPositionRetList"]
            newdata = {
                "trader_name": trader_name,
                "len_pos": len(jsdata),
                "pos": {d["symbol"]: d["amount"] for d in jsdata},
                "ent_prices": {d["symbol"]: d["entryPrice"] for d in jsdata},
            }
            # print(jsdata, newdata)

            TracksDB.update_track_data(json.dumps(newdata), trader["id"])
            olddata = json.loads(trader["data"])
            if (not isinstance(olddata["pos"], dict)) or "pos" not in olddata:
                return
            if olddata != newdata:
                changes = []
                for nd in newdata["pos"].keys():
                    tiker = nd
                    chgName = 'Long' if newdata["pos"][nd] > 0 else 'Short'
                    ent_price = "%.3f" % newdata["ent_prices"][nd]
                    # Position opening
                    if nd not in olddata["pos"]:
                        changes.append(f'⭐ __{tiker}__ {chgName} !OPENED! (Entry price: {ent_price})')
                    # Position diff calc
                    if nd in olddata["pos"] and \
                            newdata["pos"][nd] != olddata["pos"][nd]:
                        diff = (newdata["pos"][nd] - olddata["pos"][nd]) / olddata["pos"][nd] * 100
                        emj = '🔼' if diff > 0 else '🔽'
                        diff = format_float(diff)
                        changes.append(f'{emj} {tiker} {chgName}, position {diff}% (Entry price: {ent_price})')
                # Position closing
                try:
                    for od in olddata["pos"].keys():
                        chgName = 'Long' if olddata["pos"][od] > 0 else 'Short'
                        if od not in newdata["pos"]:
                            changes.append(f'🚫 {od} {chgName} !CLOSED!')
                except:
                    pass
                if not changes:
                    return
                print(changes)
                # Sending
                await bot.send_message(chat_id=CHAT_ID, text='Trader: {} has {} positions\n\n'
                                       .format(newdata["trader_name"], newdata["len_pos"]) + '\n'.join(changes),
                                       parse_mode="Markdown"
                                       )


# ============= TIMER ============= #

def timer_startup():
    loop_bot = asyncio.get_event_loop()
    loop_bot.create_task(scheduled(REFRESH_RATE, parse))


async def scheduled(wait_for, func):
    while True:
        await asyncio.sleep(wait_for)
        await func()


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
    ])


if __name__ == "__main__":
    print("Binanser started")
    timer_startup()
    executor.start_polling(dp, on_startup=on_startup,
                           on_shutdown=shutdown)
