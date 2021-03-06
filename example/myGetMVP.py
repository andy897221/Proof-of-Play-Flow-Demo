import numpy as np

def getMVP(matchData):
    """
    use highest parameter based total parameter values of all players
    :param matchData: any data type to process by your function
    :return: pub key of the winner, in string
    """

    enum = ["gold_per_min", "xp_per_min", "kills_per_min", "last_hits_per_min", "hero_damage_per_min",
            "hero_healing_per_min", "tower_damage", "stuns_per_min"]
    ratingBase = []
    team1Wins = matchData[1]
    matchData = matchData[0]

    for key, item in matchData.items():
        ratingBase += [[matchData[key][j] for j in enum]]
    ratingBase = list(np.asarray(ratingBase).sum(axis=0))

    plyrWins = {}
    for key, item in matchData.items():
        if matchData[key]["isRadiant"] and team1Wins: plyrWins[key] = True
        elif matchData[key]["isRadiant"] and not team1Wins: plyrWins[key] = False
        elif not matchData[key]["isRadiant"] and team1Wins: plyrWins[key] = False
        elif not matchData[key]["isRadiant"] and not team1Wins: plyrWins[key] = True

    plyrRating, plyrParam, plyrKey = [], [], []
    for key, item in matchData.items():
        if not plyrWins[key]: continue
        plyrallParam = [(matchData[key][enum[j]] / ratingBase[j]) if ratingBase[j] != 0 else 0 for j in
                        range(0, len(enum))]
        plyrParam += [enum[int(np.argmax(plyrallParam))]]
        plyrRating += [max(plyrallParam)]
        plyrKey += [key]

    mvpKey = plyrKey[np.argmax(np.asarray(plyrRating))]
    return mvpKey