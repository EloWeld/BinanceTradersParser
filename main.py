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
from filters import IsAdmin, IsPrivate
from states import *
import bs4

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

minute_msgs = False
is_parsing = 0
is_posting = 0


# ============= CALLBACKS ============= #
@dp.callback_query_handler(lambda c: "delete:" in c.data)
async def callbacks(cb: CallbackQuery):
    link = cb.data.split(':')[1]
    TracksDB.delete_trader(link)
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
    await bot.send_message(chat_id=CHANNEL, text=message.text)
    await state.finish()


# endregion

# region CHANGE CHANNEL

@dp.message_handler(Command('change_channel'), IsAdmin(), IsPrivate())
@dp.message_handler(Text('🍁 Изменить канал'), IsAdmin(), IsPrivate())
async def btnChangeChannel(message: types.Message):
    await message.answer(MSG["CHANGE_CH_MSG"])
    state = dp.current_state(user=message.from_user.id)
    await state.set_state("change_channel")


@dp.message_handler(IsAdmin(), IsPrivate(), state="change_channel")
async def stateChangeChannel(message: types.Message, state: FSMContext):
    try:
        test_chat = message.text
        msg = await bot.send_message(chat_id=test_chat, text=MSG["TEST_CHAT"])
        await asyncio.sleep(0.5)
        await msg.delete()
        await message.answer(text=MSG["CHAT_ACCEPTED"])
        os.putenv("CHANNEL", test_chat)
        os.environ["CHANNEL"] = test_chat
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
    global is_parsing
    global is_posting
    t = '=== CONFIG ===' + '\n'
    t += f'TIME: {os.getenv("POSTING_TIME")}' + '\n'
    t += f'CHANNEL: {os.getenv("CHANNEL")}' + '\n'
    t += f'REFRESH_RATE: {os.getenv("REFRESH_RATE")}' + '\n'
    t += f'ACCUR: {os.getenv("ACCUR")}' + '\n'
    t += '---------' + '\n'
    t += f'PARSING: {is_parsing}' + '\n'
    t += f'POSTING: {is_posting}' + '\n'
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

    await bot.send_message(chat_id=CHANNEL, text=title + description + footer, parse_mode=ParseMode.HTML)


async def process_info():
    global minute_msgs
    global is_posting
    is_posting += 1
    if not minute_msgs:
        from datetime import datetime
        c_time = ':'.join(str(datetime.now().time()).split(':')[:2])
        pt = os.getenv("POSTING_TIME")
        if c_time != pt:
            return
        else:
            print("Posting time! YO!")
            minute_msgs = True
            traders = TracksDB.get_traders()
            for trader in traders:
                # Get trader name
                trader_name = get_nickanme(trader)
                # Check posting time
                await send_trader_info(trader, trader_name)


async def parse():
    await process_info()

    global is_parsing
    is_parsing += 1

    traders = TracksDB.get_traders()
    for trader in traders:
        print(trader)
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
                await bot.send_message(chat_id=os.getenv("CHANNEL"),
                                       text=MSG["POST_TITLE"].format(trader_name, n_data["len"]) + '\n'.join(changes),
                                       parse_mode=ParseMode.HTML
                                       )
            else:
                print('No Changes')
                print('=' * 50)


# ============= TIMER ============= #

async def minute_timer():
    global minute_msgs
    minute_msgs = False


async def scheduled(delay, interval, func):
    await asyncio.sleep(delay)
    while True:
        await func()
        await asyncio.sleep(interval)


# ============= STARTUP ============= #
async def on_startup(dp):
    await set_default_commands(dp)
    for admin in [x["tgid"] for x in UsersDB.all_users() if x["role"] == 1]:
        await bot.send_message(chat_id=admin, text="💫 Binanser bot strated!")


async def on_shutdown(dispatcher):
    for admin in [x["tgid"] for x in UsersDB.all_users() if x["role"] == 1]:
        await bot.send_message(chat_id=admin, text="🛑 Binanser bot shutdowned!")

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
    ])


if __name__ == "__main__":
    asyncio.ensure_future(scheduled(0, REFRESH_RATE, parse))
    asyncio.ensure_future(scheduled(0, 62, minute_timer))
    print("Binanser started")
    executor.start_polling(dp, on_startup=on_startup,
                           on_shutdown=on_shutdown)
