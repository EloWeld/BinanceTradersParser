import json
import os
from math import ceil

import requests
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import BotCommand, CallbackQuery, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, Message

from config import ROLES, IS_SERVER, SERVER_HOUR_OFFSET, TRACK_COND, ACCUR, BINANCE_BASE_URL, BINANCE_POS_URL, \
    BINANCE_PERF_URL, is_parsing, is_posting, MSG_S
from database import *
from filters import IsAdmin, IsPrivate
from states import *

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


# ============= CALLBACKS ============= #
@dp.callback_query_handler(lambda c: "DELETE:" in c.data)
async def callbacks(cb: CallbackQuery):
    await cb.answer()
    print("Deleting trader")
    print(TracksDB.get_traders())

    trader_id = int(cb.data.split(':')[1])
    TracksDB.delete_trader(trader_id)

    print(TracksDB.get_traders())
    await cb.message.delete()


# ============= HANDLERS ============= #

@dp.message_handler(IsPrivate(), CommandStart())
async def cmdStart(message: types.Message):
    await message.answer(MSG["MOTO"], reply_markup=nav.main_menu)
    try:
        UsersDB.add_user(int(message.chat.id), message.from_user.username)
    except Exception as e:
        print(f'User {message.from_user.username} already registered!')


@dp.message_handler(IsPrivate(), Command('add_to_track'))
@dp.message_handler(IsPrivate(), Text('➕ Добавить ссылку на трек'))
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


@dp.message_handler(Command('users'), IsAdmin(), IsPrivate())
@dp.message_handler(Text('🤼‍♂️ Пользователи'), IsAdmin(), IsPrivate())
async def btnAddToTrack(message: types.Message):
    await message.answer(MSG["USERS"], reply_markup=get_users_keyboard())


# region SCREAM

@dp.message_handler(Command('scream_chat'), IsAdmin(), IsPrivate())
@dp.message_handler(Text('🔊 Покричать'), IsAdmin(), IsPrivate())
async def btnScreamChat(message: types.Message):
    await message.answer("Отправь текст")
    state = dp.current_state(user=message.from_user.id)
    await state.set_state("scream")


@dp.message_handler(IsAdmin(), IsPrivate(), state="scream")
async def stateScreamChat(message: types.Message, state: FSMContext):
    await bot.send_message(chat_id=os.environ["CHANNEL"], text=message.text)
    await state.finish()


# endregion

# region CHANGE CHANNEL

@dp.message_handler(Command('change_channel'), IsAdmin(), IsPrivate())
@dp.message_handler(Text('🍁 Изменить канал'), IsAdmin(), IsPrivate())
async def btnChangeChannel(message: types.Message):
    await message.answer(MSG["CHANGE_CH_MSG"])
    await MenuStates.ChannelChange.set()


@dp.message_handler(IsAdmin(), IsPrivate(), state=MenuStates.ChannelChange)
async def stateChangeChannel(message: types.Message, state: FSMContext):
    global CHANNEL
    try:
        test_chat = message.text
        msg = await bot.send_message(chat_id=test_chat, text=MSG["TEST_CHAT"])
        await asyncio.sleep(0.5)
        await msg.delete()
        await message.answer(text=MSG["CHAT_ACCEPTED"])
        os.putenv("CHANNEL", test_chat)
        os.environ["CHANNEL"] = test_chat
        CHANNEL = test_chat
        if os.name == 'nt' and not IS_SERVER:
            import dotenv
            dotenv_file = dotenv.find_dotenv()
            dotenv.load_dotenv(dotenv_file)
            dotenv.set_key(dotenv_file, "CHANNEL", os.environ["CHANNEL"])
        await state.finish()
    except Exception as e:
        await message.answer(text=MSG["CHAT_REJECTED"])
        print(e)
        await state.finish()


# endregion

# region CHANGE POSTING TIME

@dp.message_handler(Command('change_time'), IsAdmin(), IsPrivate())
@dp.message_handler(Text('⌚ Изменить время'), IsAdmin(), IsPrivate())
async def btnChangeTime(message: types.Message):
    await message.answer(MSG["CHANGE_TIME_MSG"])
    state = dp.current_state(user=message.from_user.id)
    await state.set_state("change_time")


@dp.message_handler(IsAdmin(), IsPrivate(), state="change_time")
async def stateChangeTime(message: types.Message, state: FSMContext):
    try:
        test_chat = message.text
        hoffset = 0 if os.name == 'nt' and not IS_SERVER else SERVER_HOUR_OFFSET
        hours = str((int(test_chat.split(':')[0]) + hoffset) % 24).zfill(2)
        mins = str(int(test_chat.split(':')[1]) % 60).zfill(2)
        os.putenv("POSTING_TIME", f'{hours}:{mins}')
        os.environ["POSTING_TIME"] = f'{hours}:{mins}'

        if os.name == 'nt' and not IS_SERVER:
            import dotenv
            dotenv_file = dotenv.find_dotenv()
            dotenv.load_dotenv(dotenv_file)
            dotenv.set_key(dotenv_file, "POSTING_TIME", os.environ["POSTING_TIME"])

        await message.answer(text=MSG["TIME_ACCEPTED"].format(f'{hours}:{mins}'))
        await state.finish()
    except Exception as e:
        await message.answer(text="Не вышло изменить время")
        print(e)
        await state.finish()


# endregion

@dp.message_handler(Command('all_tracks'), IsPrivate())
@dp.message_handler(Text('📃 Трек'), IsPrivate())
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


@dp.errors_handler()
async def errors_handler(update, exception):
    for admin_id in [x["tgid"] for x in UsersDB.all_admins()]:
        await bot.send_message(admin_id, text="⛔ Ошибка: " + str(exception.args))


@dp.message_handler(IsPrivate(), Command('config'), IsAdmin())
async def stateCommand(message: types.Message):
    import config
    t = '=== CONFIG ===' + '\n'
    t += f'TIME: {os.getenv("POSTING_TIME")}' + '\n'
    t += f'CHANNEL: {os.getenv("CHANNEL")}' + '\n'
    t += f'REFRESH_RATE: {os.getenv("REFRESH_RATE")}' + '\n'
    t += f'ACCUR: {os.getenv("ACCUR")}' + '\n'
    t += '---------' + '\n'
    t += f'PARSING: {config.get_parsing_iteration()}' + '\n'
    t += f'POSTING: {config.get_posting_iteration()}' + '\n'
    t += '=== ===== ===' + '\n'
    await message.answer(text=t)


@dp.message_handler(IsPrivate(), state=MenuStates.Command)
async def stateCommand(message: types.Message, state: FSMContext):
    # Filter
    if TRACK_COND in message.text:
        TracksDB.add_trader(message.text)

        await message.answer(MSG["TRACK_ADDED"])

    else:
        await message.answer(f'Некорректная ссылка! \nУсловие: {TRACK_COND}')

    await state.finish()


@dp.message_handler(IsPrivate(), Command('chatid'))
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

    try:
        a = session.post(url=BINANCE_BASE_URL, data=json.dumps(payload), headers=head)
        if a.status_code != 200 or (not a.json()) or ("data" not in a.json()) or a.json()["data"] is None:
            return "Noname"
    except:
        return "Noname"
    return a.json()["data"]["nickName"]


def get_trader_positions(trader):
    encUid = trader["link"].split('encryptedUid=')[1]
    payload = {
        "encryptedUid": encUid, "tradeType": "PERPETUAL"
    }
    response = session.post(BINANCE_POS_URL, data=json.dumps(payload), headers=head)
    if (not response) or response.status_code != 200 or \
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
    print(roe_stat)
    return roe_stat, pnl_stat


async def send_trader_info(trader, t_name: str):
    roe, pnl = get_trader_performance(trader)
    title = MSG["TRADER_INFO_TITLE"].format(t_name)
    description = ''
    for r in roe:
        if r != 'ALL':  # Да, да, блять, костыли, ну и похуй
            description += f'<b>{MSG_S[r]}</b>: {format_float(roe[r] * 100, 2)}% \n'

    footer = f"==============\n"

    await bot.send_message(chat_id=os.environ["CHANNEL"], text=title + description + footer, parse_mode=ParseMode.HTML)


@dp.message_handler(IsAdmin(), Text("Отчёт"))
async def start_broadcast(message: Message = None):
    traders = TracksDB.get_traders()
    for trader in traders:
        # Get trader name
        trader_name = get_nickanme(trader)
        # Check posting time
        await send_trader_info(trader, trader_name)


# ============= STARTUP ============= #
async def on_startup(dp):
    await set_default_commands(dp)


async def on_shutdown(dispatcher):

    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()



async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        BotCommand("all_tracks", "Посмотреть трек"),
        BotCommand("add_to_track", "Добавить в трек линку"),
        BotCommand("users", "Список юзеров"),
        BotCommand("scream_chat", "Покричать что-то в чат/канал"),
        BotCommand("change_channel", "Изменить канал"),
        BotCommand("change_time", "Изменить время постинга"),
        BotCommand("config", "Конфигурационные данные бота и статистика"),
        BotCommand("chatid", "Чат ID"),
    ])


if __name__ == "__main__":
    print("Binanser started")
    executor.start_polling(dp, on_startup=on_startup,
                           on_shutdown=on_shutdown)
