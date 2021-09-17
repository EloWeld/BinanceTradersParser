import os
from enum import Enum

from dotenv import load_dotenv

load_dotenv()
PSDB = dict(name="nqywnhxr", user="nqywnhxr",
            pwd="6IqMyfxZPssKoafad39w8Lsiytyb-JDO",
            host="chunee.db.elephantsql.com",
            port="5432")
DB_CREDS = Enum('ElephCredentails', PSDB)

TOKEN = os.getenv('TOKEN')
CHAT = os.getenv('CHAT')
CHANNEL_ID = os.getenv('CHANNEL')
ACCUR = os.getenv('ACCUR')
POSTING_TIME = os.getenv('POSTING_TIME')
REFRESH_RATE = int(os.getenv('REFRESH_RATE'))
TRACK_COND = 'encryptedUid'
BINANCE_POS_URL = 'https://www.binance.com/bapi/futures/v1/public/future/leaderboard/getOtherPosition'
BINANCE_PERF_URL = 'https://www.binance.com/bapi/futures/v1/public/future/leaderboard/getOtherPerformance'
BININCE_PAGE_URL = 'https://www.binance.com/ru/futures-activity/leaderboard?type=myProfile&tradeType=PERPETUAL' \
                   '&encryptedUid= '
BINANCE_BASE_URL = 'https://www.binance.com/bapi/futures/v2/public/future/leaderboard/getOtherLeaderboardBaseInfo'

ROLES = {
    0: 'Юзер',
    1: "Админ"
}

MSG_S = dict(DAILY="Ежедневно",
             EXACT_WEEKLY="Последние 7 дней",
             EXACT_MONTHLY="Последние 30 дней",
             EXACT_YEARLY="Последние 12 мес.",
             WEEKLY="Еженедельно",
             MONTHLY="Ежемесячно",
             YEARLY="Годовой",
             ALL="Всё время")

MSG = dict(MOTO="Здарова, вот твой бот. Короче скинь ему ссылку на страницу с позициями, чтобы он её трекерил",
           USERS="Вот список всех пользователей бота, нажмите чтобы изменить права",
           GET_ROLE="ℹ Вам была назначена роль: {0}",
           TRACK_ADDED="Трек добавлен в список ✅",
           TRADER_INFO_TITLE="ℹ<b><u>{0}</u></b> daily statement: \n==============\n",
           OPENED="⭐ <b>{0}</b> <i>{1}</i> !OPENED! (Entry price: {2})",
           CLOSED="🚫 <b>{0}</b> <i>{1}</i> !CLOSED!",
           CHANGE="{0} <b>{1}</b> <i>{2}</i>, position {3}% (Entry price: {4})",
           POST_TITLE="Трейдер: <b>{0}</b> имеет <b>{1}</b> позиции\n\n",
           TEST_CHAT="Тук-тук, кто там?",
           CHANGE_CH_MSG="📧 Отправь номер канала",
           CHAT_REJECTED="Ой. Не могу ничего отправить в тот чат :с",
           CHAT_ACCEPTED="Чат для постинга изменён",
           CHANGE_TIME_MSG="⌛ Отправь новое время для постинга в формате ХХ:ХХ",
           TIME_ACCEPTED="Время изменено на {}. \nТеперь в это время будет поститься статистика по каждому трейдеру")
