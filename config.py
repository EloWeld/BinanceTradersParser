import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')
CHAT_ID = os.getenv('CHAT')
ACCUR = os.getenv('ACCUR')
REFRESH_RATE = int(os.getenv('REFRESH_RATE'))
TRACK_COND = 'encryptedUid'
BINANCE_API_URL = 'https://www.binance.com/bapi/futures/v1/public/future/leaderboard/getOtherPosition'
BININCE_PAGE_URL = 'https://www.binance.com/ru/futures-activity/leaderboard?type=myProfile&tradeType=PERPETUAL' \
                   '&encryptedUid= '

MSG = {
    "MOTO": "Здарова, вот твой бот. Короче скинь ему ссылку на страницу с позициями, чтобы он её трекерил",
}
