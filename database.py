import sqlite3
import psycopg2

from config import DB_CREDS


class Database:
    def __init__(self, path_to_db="Data.db"):
        super(Database, self).__init__()
        self.path_to_db = path_to_db

    @property
    def connection(self):
        return psycopg2.connect(dbname=DB_CREDS.name.value,
                                user=DB_CREDS.user.value,
                                password=DB_CREDS.pwd.value,
                                host=DB_CREDS.host.value)

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
        sql = 'INSERT INTO users(tgid, username) VALUES (%s, %s)'
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
        sql = 'SELECT role FROM users ' \
              'WHERE tgid = %s'
        params = (user_tgid,)
        data = self.execute(sql, params, fetchone=True)
        return data[0]

    def change_role(self, user_tgid, newrole):
        sql = 'UPDATE users ' \
              'SET role = %s ' \
              'WHERE tgid = %s'
        params = (newrole, user_tgid)
        data = self.execute(sql, params, commit=True)
        return data


class TracksDatabase(Database):
    def add_trader(self, link: str):
        sql = 'INSERT INTO traders(link) VALUES (%s)'
        params = (link,)
        data = self.execute(sql, params, commit=True)
        return data

    def get_traders(self):
        sql = 'SELECT * FROM traders'
        data = self.execute(sql, fetchall=True)
        if not data or len(data) == 0:
            return []
        d = [{
            'data': x[0],
            'pos': x[1],
            'id': x[2],
            'link': x[3],
        } for x in data]
        return d

    def delete_trader(self, x):
        sql = 'DELETE FROM traders ' \
              'WHERE id = %s'
        params = (x,)
        self.execute(sql, params, commit=True)

    def update_trader_data(self, newdata, trackid):
        sql = 'UPDATE traders ' \
              'SET data = %s ' \
              'WHERE id = %s'
        params = (str(newdata), int(trackid))
        self.execute(sql, params, commit=True)


TracksDB = TracksDatabase()
UsersDB = UsersDatabase()
