import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')
CHAT_ID = os.getenv('CHAT')
CHANNAL_ID = os.getenv('CHANNAL')
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

MSG = dict(MOTO="Здарова, вот твой бот. Короче скинь ему ссылку на страницу с позициями, чтобы он её трекерил",
           USERS="Вот список всех пользователей бота, нажмите чтобы изменить права",
           GET_ROLE="ℹ Вам была назначена роль: {0}",
           TRACK_ADDED="Трек добавлен в список ✅",
           TRADER_INFO_TITLE="ℹ<b><u>{0}</u></b> daily statement: \n==============\n",
           OPENED="⭐ <u>{0}</u> <i>{1}</i> !OPENED! (Entry price: {2})",
           CLOSED="🚫 {0} {1} !CLOSED!",
           CHANGE="{0} <u>{1}</u> <i>{2}</i>, position {3}% (Entry price: {4})",
           POST_TITLE="Трейдер: <b>{0}</b> имеет <b>{1}</b> позиции\n\n")
