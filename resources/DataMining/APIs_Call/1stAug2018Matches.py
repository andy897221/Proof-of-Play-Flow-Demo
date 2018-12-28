import math, time, requests, json

url = 'https://api.opendota.com/api/explorer?sql={}'
SQL = "SELECT * FROM public_matches WHERE lobby_type = 7 and game_mode = 22 and start_time >= 1533081600 order by start_time LIMIT {}"
limit = 500000
null = None
false = False
is2ndAug = False
output = open('1stAug2018Matches.txt', 'a+')
counter = 0
listOfMatches = []

while not is2ndAug:
    curSQL = SQL.format(limit+(limit*counter))
    res = json.loads(requests.get(url.format(curSQL)).text)
    try:
        matchList = res["rows"]
        for match in matchList:
            if match["start_time"] >= 1533168000:
                is2ndAug = True
                break
            else: listOfMatches += [match]
    except Exception as e:
        print(e)
        time.sleep(60)
        continue
    counter += 1
    time.sleep(10)
    print("first loop ended")
print("loop ended")    

output.write(json.dumps(listOfMatches))
output.close()