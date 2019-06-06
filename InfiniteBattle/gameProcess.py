import json

# def getPubKey(bytes_string):
#     pubkey = ""
#     for s in bytes_string.decode().split('\n'):
#         if ("PUBLIC KEY" in s):
#             continue
#         pubkey = pubkey + s
#     return pubkey

def importGameResult(fileContent, playerList):
    content = json.loads(fileContent)
    
    matchData = dict()
    players = sorted(content.keys())
    for player in players:
        matchData[player] = content[player]

    if(len(players) != len(playerList)):
        return None
    
    # for i in range(len(playerList)):
    #     playerList[i] = getPubKey(playerList[i])

    for player in players:
        if player not in playerList:
            return None
        playerList.remove(player)

    return matchData

def getRating(matchData, plyrPubKey): 
    minn_total = 1 << 31
    for key, item in matchData.items():
        minn_total = min(minn_total, item["AmountOfHarm"] + item["AmountOfBear"] + item["AmountOfRescue"])
    
    plyrData = matchData[plyrPubKey]
    score = plyrData["Killed"] / (plyrData["Death"] + 1) + (plyrData["AmountOfHarm"] + plyrData["AmountOfBear"] + plyrData["AmountOfRescue"]) / minn_total

    if(plyrData["IsWinner"]):
        score = score * 1.6
    
    # print(plyrPubKey, score)
    return float(round(score, 2))

def getMVP(matchData):
    highestRate = -1
    mvpKey = None

    for key, item in matchData.items():
        if(item["IsWinner"]):
            score = getRating(matchData, key)
            if(highestRate < score):
                highestRate = score
                mvpKey = key
            elif (highestRate == score):
                if (matchData[mvpKey]["Killed"] > item["Killed"]):
                    pass
                elif (matchData[mvpKey]["Death"] < item["Death"]):
                    pass
                elif (matchData[mvpKey]["AmountOfHarm"] > item["AmountOfHarm"]):
                    pass
                elif (matchData[mvpKey]["AmountOfBear"] > item["AmountOfBear"]):
                    pass
                elif (matchData[mvpKey]["AmountOfRescue"] > item["AmountOfRescue"]):
                    pass
                elif (mvpKey < key):
                    pass
                else:
                    mvpKey = key

    return mvpKey

# if __name__ == "__main__":
#     f = open("player.result", "r")
#     matchData = json.loads(f.read())
#     print("MVP:", getMVP(matchData))