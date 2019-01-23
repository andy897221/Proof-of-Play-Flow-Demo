import numpy as np

def getMVP(self):
    # use highest parameter based total parameter values of all players
    enum = ["gold_per_min", "xp_per_min", "kills_per_min", "last_hits_per_min", "hero_damage_per_min",
            "hero_healing_per_min", "tower_damage", "stuns_per_min"]
    plyrRating, ratingBase = {"param": [], "rating": []}, []
    team1Wins = self.matchData[1]
    matchData = self.matchData[0]

    for key, item in matchData.item():
        ratingBase += [[matchData[key][j] for j in enum]]
    ratingBase = list(np.asarray(ratingBase).sum(axis=0))

    for key, item in matchData.item():
        plyrallParam = [(matchData[key][enum[j]] / ratingBase[j]) if ratingBase[j] != 0 else 0 for j in
                        range(0, len(enum))]
        plyrRating["param"] += [enum[int(np.argmax(plyrallParam))]]
        plyrRating["rating"] += [max(plyrallParam)]
    plyrRating_np = np.asarray(plyrRating["rating"])

    plyrWins = []
    for key, item in matchData.item():
        if matchData[key]["isRadiant"] and team1Wins: plyrWins += [True]
        elif matchData[key]["isRadiant"] and not team1Wins: plyrWins += [False]
        elif not matchData[key]["isRadiant"] and team1Wins: plyrWins += [False]
        elif not matchData[key]["isRadiant"] and not team1Wins: plyrWins += [True]
    plyrWins = np.asarray(plyrWins)

    mvpIndex = np.where(plyrWins == True)[0][np.argmax(plyrRating_np[plyrWins])]
    return mvpIndex