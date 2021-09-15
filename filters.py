from aiogram import types
from aiogram.dispatcher.filters import BoundFilter

from database import UsersDatabase, UsersDB


class IsAdmin(BoundFilter):
    async def check(self, message: types.Message, *args) -> bool:
        admin = message.from_user.id in [x["tgid"] for x in UsersDB.all_admins()]
        return admin