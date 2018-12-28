# 1st Aug 2018 to 31st Aug 2018
import math, time, requests

url = 'https://api.opendota.com/api/explorer?sql={}'
SQL = "Select * from public_matches WHERE lobby_type = 7 and game_mode = 22 and start_time >= {} and start_time < {} ORDER BY match_id LIMIT {}, {}"
month_start_time = 1533081600
month_end_time = 1535760000
offsetUnit = 30000
TotalMatches = 3289132

for offset in range(1, math.ceil(TotalMatches/offsetUnit)+1):
    if offsetUnit*offset > TotalMatches:
        curOffset = TotalMatches-(offsetUnit*(offset-1))
    else:
        curOffset = offsetUnit
    curSQL = SQL.format(month_start_time, month_end_time, curOffset, (offset-1)*offsetUnit)
    print(requests.get(url.format(curSQL), ))
    
    break