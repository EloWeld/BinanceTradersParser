import json
import os
from datetime import timedelta

import requests

url = 'https://www.binance.com/bapi/futures/v2/public/future/leaderboard/getOtherLeaderboardBaseInfo'
payload = {
  "encryptedUid": "94483211BC036EDD2B0808F7C04420E8"
}
head = {
    'authority': 'www.binance.com',
    'content-type': 'application/json',
    'accept': '*/*',
}

a = requests.post(url=url, data=json.dumps(payload), headers=head)
print(a.json()["data"]["nickName"])
print(timedelta(hours=96, minutes=55).seconds / 60 % 60, )