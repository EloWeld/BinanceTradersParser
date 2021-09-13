import asyncio

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters import Text, CommandStart, Command
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils import executor

import nav
from config import TOKEN, REFRESH_RATE, MSG
from database import TracksDatabase


class MenuStates(StatesGroup):
    Command = State()
