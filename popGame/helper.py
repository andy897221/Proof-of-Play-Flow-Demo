class plyrResList:
    def __init__(self, matchData, winnerFunc, pubKeyList):
        self.matchData = matchData
        self.mvpKey = winnerFunc(self.matchData)
        self.pubKeyList = pubKeyList
        self.signature = None # <class plyrData.plyrSignRes>, given post-cross-verify

    def __eq__(self, other):
        return self.matchData == other.matchData and self.mvpKey == other.mvpKey

    def returnMVP(self):
        return self.mvpKey

    def returnMatchData(self):
        return self.matchData

    def returnPubKeyList(self):
        return self.pubKeyList

    def returnSignature(self):
        return self.signature

    def verify_signature(self, listOfPubKey):
        return