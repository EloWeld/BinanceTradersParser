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

chats = set()


# ============= CALLBACKS ============= #
@dp.callback_query_handler(lambda c: "delete:" in c.data)
async def callbacks(cb: CallbackQuery):
    link = cb.data.split(':')[1]
    TracksDB.delete_track(link)
    await cb.message.delete()


# ============= HANDLERS ============= #

@dp.message_handler(CommandStart())
async def cmdStart(message: types.Message):
    await message.answer(MSG["MOTO"], reply_markup=nav.main_menu)
    UsersDB.add_user(int(message.chat.id), message.from_user.username)


@dp.message_handler(Command('add_to_track'))
@dp.message_handler(Text('➕ Добавить ссылку на трек'))
async def btnAddToTrack(message: types.Message):
    await message.answer("Оптравь ссылку на трек ✉")

    await MenuStates.Command.set()


@dp.message_handler(Command('all_track'))
@dp.message_handler(Text('📃 Трек'))
async def btnAllTrack(message: types.Message):
    tracks = TracksDB.get_tracks()

    if not tracks:
        await message.answer('Треков нет')
        return
    else:
        await message.answer("Вот все треки")

        for tr in tracks:
            await message.answer(text=f'Id: {tr["id"]}\n'
                                      f'Link: {tr["link"]}\n'
                                      f'Rating: {tr["rating"]}\n'
                                      f'Position: {tr["pos"]}\n',
                                 reply_markup=nav.track_menu(tr["id"]))


@dp.message_handler(state=MenuStates.Command)
async def stateCommand(message: types.Message, state: FSMContext):
    # Filter
    if TRACK_COND in message.text:
        TracksDB.add_to_track(message.text)

        await message.answer("Ок, добавил")

    else:
        await message.answer(f'Некорректная ссылка! \nУсловие: {TRACK_COND}')

    await state.finish()


# ============= PARSING ============= #
head = {
    'authority': 'www.binance.com',
    'content-type': 'application/json',
    'accept': '*/*',
}
session = requests.session()
session.headers.update(head)

async def parse():
    tracks = TracksDB.get_tracks()
    for track in tracks:
        encUid = track["link"].split('encryptedUid=')[1]
        payload = {
            "encryptedUid": encUid, "tradeType": "PERPETUAL"
        }
        response = session.post(BINANCE_API_URL, data=json.dumps(payload), headers=head)
        if response and response.json() and response.json()["data"]:
            jsdata = response.json()["data"]["otherPositionRetList"]
            data = {
                "user_id": encUid,
                "len_pos": len(jsdata),
                "pos": [{
                    "name": d["symbol"],
                    "percent": d["roe"],
                } for d in jsdata],
            }

            [data["pos"].append({
                "name": d["symbol"],
                "percent": d["roe"],
            }) for d in jsdata]

            TracksDB.update_track_data(json.dumps(data), track["id"])
            if track["data"] != json.dumps(data):
                print(track["data"])
                print(json.dumps(data))
                print("==============================")
                # Sending
                for chat in chats:
                    crptid = data["user_id"][:4] + '***' + data["user_id"][-4:]
                    await bot.send_message(chat_id=chat, text='Uid: {} has {} positions\n'
                                           .format(crptid, data["len_pos"]) + '\n'.join(
                        [
                            f'⭐{x["name"]} precent {x["percent"]}' for x in data["pos"]
                        ]
                    )
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

    for item in UsersDB.all_users():
        chats.add(item["tgid"])


async def shutdown(dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        BotCommand("all_track", "Посмотреть трек"),
        BotCommand("add_to_track", "Добавить в трек линку"),
    ])


if __name__ == "__main__":
    print("Binanser started")
    timer_startup()
    executor.start_polling(dp, on_startup=on_startup,
                           on_shutdown=shutdown)
