import asyncio

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import ReplyKeyboardMarkup as Menu, InlineKeyboardMarkup as InlKeyboard, \
    InlineKeyboardButton as InlineBtn
from aiogram.types import KeyboardButton as Btn
from aiogram.utils import executor

from config import TOKEN, REFRESH_RATE, MSG

main_menu = Menu(resize_keyboard=True, keyboard=[
    [
        Btn('➕ Добавить ссылку на трек'),
        Btn('📃 Трек')
    ]
])


def track_menu(data: str):
    return InlKeyboard(inline_keyboard=[
        [
            InlineBtn(text='Удалить ❌', callback_data=f'delete:{data}'),
            # InlineBtn(text='Заменить ссылку ⏪', callback_data=f'rewrite:{data}')
        ]
    ])
