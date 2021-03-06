import numpy as np

def getRating(matchData, plyrPubKey):
    # the matchData is formatted as {pubKey: {rating: int,...},...}
    """
        use highest parameter based total parameter values of all players
        :param matchData: any data type to process by your function
        :param plyrPubKey: to get the rating of this match, str
        :return: the rating of the player, float
        """

    enum = ["gold_per_min", "xp_per_min", "kills_per_min", "last_hits_per_min", "hero_damage_per_min",
            "hero_healing_per_min", "tower_damage", "stuns_per_min"]
    ratingBase = []
    matchData = matchData[0]

    for key, item in matchData.items():
        ratingBase += [[matchData[key][j] for j in enum]]
    ratingBase = list(np.asarray(ratingBase).sum(axis=0))

    plyrallParam = [(matchData[plyrPubKey][enum[j]] / ratingBase[j]) if ratingBase[j] != 0 else 0 for j in
                    range(0, len(enum))]
    plyrRating = max(plyrallParam)

    return float(plyrRating)