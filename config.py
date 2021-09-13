import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')
REFRESH_RATE = 15
TRACK_COND = 'encryptedUid'
BINANCE_API_URL = 'https://www.binance.com/bapi/futures/v1/public/future/leaderboard/getOtherPosition'

MSG = {
    "MOTO": "Здарова, вот твой бот. Короче скинь ему ссылку на страницу с позициями, чтобы он её трекерил",
}
