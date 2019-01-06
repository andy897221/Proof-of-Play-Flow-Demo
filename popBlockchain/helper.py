import numpy as np
import requests

class helper:
    def get_rating(matchData, plyrIndex):
        enum = ["gold_per_min", "xp_per_min", "kills_per_min", "last_hits_per_min", "hero_damage_per_min", "hero_healing_per_min", "tower_damage", "stuns_per_min"]
        plyrRating, ratingBase = {"param": 0, "rating": 0}, []
        for i in range(0, len(matchData)):
            ratingBase += [[matchData[i][j] for j in enum]]
        ratingBase = list(np.asarray(ratingBase).sum(axis=0))

        plyrallParam = [(matchData[plyrIndex][enum[j]] / ratingBase[j]) if ratingBase[j] != 0 else 0 for j in range(0, len(enum))]
        plyrRating["param"] = [enum[np.argmax(plyrallParam)]]
        plyrRating["rating"] = max(plyrallParam)
        return plyrRating["rating"], plyrRating["param"]

    def get_total_rating(matchData, plyrPubKey):
        totalRating = 0
        for match in matchData:
            plyrIndex = np.where(np.asarray(match['plyrAddrList']) == plyrPubKey)[0]
            if len(plyrIndex) == 0: continue
            plyrIndex = plyrIndex[0]
            rating, dump = helper.get_rating(match['matchData'], plyrIndex)
            totalRating += rating
            print(totalRating, rating)
        return totalRating

    def is_any_MVP(matchData, plyrPubKey):
        for match in matchData:
            if plyrPubKey == match['winnerAddr']: return True
        return False

    def broadcastResult(nodes, chain):
        for node in nodes:
            print(f"broadcasting...current node: {node}")
            res = requests.post(f"http://{node}/chain/write", json={"chain": chain})
            print(res.text)
        return

    def get_target_rating(matchesData, plyrPubKey, difficulty):
        total_rating = 0
        for match in matchesData:
            plyrIndex = np.where(np.asarray(match['plyrAddrList']) == plyrPubKey)[0]
            if len(plyrIndex) == 0: continue
            plyrIndex = plyrIndex[0]
            rating, dump = helper.get_rating(match['matchData'], plyrIndex)
            total_rating += rating
        return (total_rating / len(matchesData)) * difficulty