class plyrResList:
    def __init__(self, matchData, winnerFunc):
        self.matchData = matchData
        self.MVPIndex = winnerFunc(self.matchData)

    def __eq__(self, other):
        return self.matchData == other.matchData and self.MVPIndex == other.MVPIndex

    def returnMVP(self, plyrData):
        return plyrData.gamePlyrs[self.MVPIndex]

    def returnDict(self):
        data = {"matchData": self.matchData, "MVP": self.MVPIndex}
        return data