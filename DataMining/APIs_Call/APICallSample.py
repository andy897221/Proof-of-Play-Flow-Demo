# defined a day matches by randSampledDailyPlayerCount.py

import math, time, requests, json

url = 'https://api.opendota.com/api/explorer?sql={}'
SQL = "SELECT COUNT(match_id) FROM public_matches WHERE lobby_type = 7 and game_mode = 22 and start_time >= {} and start_time < {}"
day_start_time = 1533081600
aDay = 86400
null = None
false = False

numOfMatchPerDay = [65395, 68107, 69458, 75243, 76506, 69145, 67965, 67703, 68631, 67484, 72571, 77109, 66604, 60311, 60784, 65396, 72504, 77111, 67813, 67429, 67628, 65283, 68951, 74079, 74079, 83148, 77678, 76604, 75061, 76196, 77657]

for i in range(31,31):
    curSQL = SQL.format(day_start_time+(aDay*i), day_start_time+(aDay*(i+1)))
    res = json.loads(requests.get(url.format(curSQL)).text)
    print(res)
    numOfMatchPerDay += [res["rows"][0]["count"]]
    print(numOfMatchPerDay)
    time.sleep(1)