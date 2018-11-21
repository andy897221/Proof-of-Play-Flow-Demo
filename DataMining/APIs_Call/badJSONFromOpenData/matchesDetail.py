import math, time, requests, json
url = 'https://api.opendota.com/api/matches/{}'
match_ids = open('1stAug2018Matches.txt', 'r').read()
match_ids = json.loads(match_ids)
output = open('matchDetails.txt', 'a+', encoding='utf-8')
output.write("[")

if len(match_ids) > 20000: getMatchNum = 20000
else: getMatchNum = len(match_ids)

for match in range(0, getMatchNum):
    if match != 0: output.write(",")
    match_id = match_ids[match]["match_id"]
    curReq = url.format(match_id)
    print(curReq)
    res = requests.get(curReq).text
    output.write(str(res))
    time.sleep(10)
    
output.write("]")