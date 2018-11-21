# seems like rate is 12 per min
# 1st Aug 2017 to 2018

import math, time, requests, json, random
from statistics import mean

url = 'https://api.opendota.com/api/explorer?sql={}'
SQL = "SELECT COUNT(match_id) FROM public_matches WHERE lobby_type = 7 and game_mode = 22 and start_time >= {} and start_time < {}"
day_start_time = 1533081600
aDay = 86400
null = None
false = False
output = open('playerCountOutput.txt', 'a+')

def genValidStartTime():
    validStart = 1501545600
    return [validStart+(aDay*i) for i in range(0,365)]

def samplePlayerCount():
    global output
    validStartList = genValidStartTime()
    numOfMatchPerDay = []
    movingAvg = []
    for j in range(0,10):
        for i in range(0,7):
            randDay = random.randrange(0,len(validStartList))
            curSQL = SQL.format(validStartList[randDay], validStartList[randDay]+aDay)
            res = json.loads(requests.get(url.format(curSQL)).text)
            try:
                numOfMatchPerDay += [res["rows"][0]["count"]]
                output.write("SQL: {}\nJson return: {}\nCount: {}\n\n".format(
                    curSQL, res, numOfMatchPerDay[-1]))
                print("SQL: {}\nJson return: {}\nCount: {}\n\n".format(
                    curSQL, res, numOfMatchPerDay[-1]))
            except Exception:
                print("rate exceeds, sleep for 1 min...")
                time.sleep(60)
                curSQL = SQL.format(validStartList[randDay], validStartList[randDay]+aDay)
                res = json.loads(requests.get(url.format(curSQL)).text)
                numOfMatchPerDay += [res["rows"][0]["count"]]
                output.write("SQL: {}\nJson return: {}\nCount: {}\n\n".format(
                    curSQL, res, numOfMatchPerDay[-1]))
                print("SQL: {}\nJson return: {}\nCount: {}\n\n".format(
                    curSQL, res, numOfMatchPerDay[-1]))
            del validStartList[randDay]
            time.sleep(10)
        movingAvg += [mean(numOfMatchPerDay[7*j:7*j+7])]
    return numOfMatchPerDay, movingAvg

numOfMatchPerDay, movingAvg = samplePlayerCount()
print(numOfMatchPerDay, movingAvg)
output.write("The sampled count is: "+str(numOfMatchPerDay)+"\n")
output.write("The avg is: "+str(mean(numOfMatchPerDay))+"\n")
output.write("The avg per 10 days sample is: "+str(movingAvg)+"\n")