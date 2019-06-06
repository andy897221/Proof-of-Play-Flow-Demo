import json

def importGameResult(fileContent, plyrList):
    # format the matchData as such:
    # matchData[0] = {b"plyrPubKey": {"gold_per_min", "xp_per_min", "kills_per_min", "last_hits_per_min", "hero_damage_per_min", "hero_healing_per_min", "tower_damage", "stuns_per_min", "isRadiant"}}
    # first item of matchData is a dictionary of rating dictionary of a player
    # second item of matchData is radiantWins, a boolean value

    # this is a two player match created specific first this example

    content = json.loads(fileContent)

    return content

    # matchData = dict()
    # radiantWins = content["radiant_win"]
    # enum = ["gold_per_min", "xp_per_min", "kills_per_min", "last_hits_per_min", "hero_damage_per_min", "hero_healing_per_min", "tower_damage", "stuns_per_min"]

    # # if len(plyrList) != len(content["players"]): return False
    # for plyr in range(0, len(plyrList)):
    #     matchData[plyrList[plyr]] = {}
    #     for j in enum:
    #         matchData[plyrList[plyr]][j] = content["players"][plyr]["benchmarks"][j]["raw"]
    #     if plyr == 0: matchData[plyrList[plyr]]["isRadiant"] = True
    #     else: matchData[plyrList[plyr]]["isRadiant"] = False

    # matchData = [matchData, radiantWins]

    # return matchData