import numpy as np
import requests
import pickle, tempfile

class helper:
    matches_for_target = 10

    def __init__(self, user_rating_func, key):
        self.user_rating_func = user_rating_func
        self.key = key

    def get_total_rating(self,matchData, plyrPubKey):
        totalRating = 0
        for match in matchData:
            if plyrPubKey not in match['plyrAddrList']: continue
            rating = self.user_rating_func(match['matchData'], plyrPubKey)
            totalRating += rating
        return totalRating

    @staticmethod
    def is_any_MVP(matchData, plyrPubKey):
        for match in matchData:
            if plyrPubKey == match['winnerAddr']: return True
        return False

    def broadcastResult(self, nodes, chain):
        for node in nodes:
            if node == self.key.pubKey: continue
            print(f"broadcasting...current node: {node[27:37]}")
            for i in range(0,3):
                try:
                    res = requests.post(f"http://{nodes[node]}/chain/write", data=pickle.dumps(chain))
                    print("received message: "+res.text)
                    break
                except Exception:
                    print(f"node {nodes[node]} does not exists / is offline.")
                    print(f"retrying {i+1}...")
        return

    def get_target_rating(self, chain, plyrPubKey, difficulty):
        total_rating = 0
        matches, plyrIndex = [], []
        for block in range(len(chain)-1, -1, -1):
            block = chain[block]
            for match in block["matches"]:
                if plyrPubKey not in match['plyrAddrList']: continue
                matches += [match['matchData']]
                if len(matches) >= helper.matches_for_target: break
            if len(matches) >= helper.matches_for_target: break
        for match in range(0, len(matches)):
            rating = self.user_rating_func(matches[match], plyrPubKey)
            total_rating += rating
        if len(matches) == 0: return 0
        return (total_rating / len(matches)) * difficulty