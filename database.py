import asyncio
import sqlite3

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import ReplyKeyboardMarkup as Menu
from aiogram.types import KeyboardButton as Btn
from aiogram.utils import executor

from config import TOKEN, REFRESH_RATE, MSG


class Database:
    def __init__(self, path_to_db="Data.db"):
        super(Database, self).__init__()
        self.path_to_db = path_to_db

    @property
    def connection(self):
        return sqlite3.connect(self.path_to_db)

    def execute(self, sql: str, parameters: tuple = None, fetchone=False, fetchall=False, commit=False):
        if not parameters:
            parameters = tuple()
        connection = self.connection
        cursor = connection.cursor()
        data = None
        cursor.execute(sql, parameters)
        if commit:
            connection.commit()
        if fetchone:
            data = cursor.fetchone()
        if fetchall:
            data = cursor.fetchall()
        connection.close()

        return data


class UsersDatabase(Database):
    def add_user(self, id: int, username: str):
        sql = 'INSERT INTO users(tgid, username) VALUES (?, ?)'
        params = (id, username)
        data = self.execute(sql, params, commit=True)
        return data

    def all_users(self):
        sql = 'SELECT * FROM users'
        data = self.execute(sql, fetchall=True)
        if not data or len(data) == 0:
            return []
        d = [{
            'id': x[0],
            'tgid': x[1],
            'username': x[2],
            'role': x[3],
        } for x in data]
        return d

    def all_admins(self):
        return [x for x in self.all_users() if x["role"] == 1]

    def get_role(self, user_tgid):
        sql = 'SELECT role FROM users WHERE tgid=?'
        params = (user_tgid, )
        data = self.execute(sql, params, fetchone=True)
        return data[0]

    def change_role(self, user_tgid, newrole):
        sql = 'UPDATE users SET role=? WHERE tgid=?'
        params = (newrole, user_tgid)
        data = self.execute(sql, params, commit=True)
        return data


class TracksDatabase(Database):
    def add_trader(self, link: str):
        sql = 'INSERT INTO trackers(link) VALUES (?)'
        params = (link,)
        data = self.execute(sql, params, commit=True)
        return data

    def get_traders(self):
        sql = 'SELECT * FROM trackers'
        data = self.execute(sql, fetchall=True)
        if not data or len(data) == 0:
            return []
        d = [{
            'id': x[3],
            'link': x[0],
            'data': x[1],
            'pos': x[2],
        } for x in data]
        return d

    def delete_trader(self, x):
        sql = 'DELETE FROM trackers WHERE id = ?'
        params = (x,)
        self.execute(sql, params, commit=True)

    def update_trader_data(self, newdata, trackid):
        sql = 'UPDATE trackers SET data = ? WHERE id = ?'
        params = (newdata, trackid)
        self.execute(sql, params, commit=True)


TracksDB = TracksDatabase()
UsersDB = UsersDatabase()