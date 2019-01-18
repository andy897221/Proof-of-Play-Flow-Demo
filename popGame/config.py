# namespace
class config:
    def __init__(self, p2pPort, APIPort, nodeID):
        self.port = p2pPort # my port for opening connection
        self.ID = None # my addr ID
        self.nodeID = nodeID
        self.APIPort = APIPort

class key:
    priKey = ""
    pubKey = ""

class gameConf:
    gameOn = False # lock adding players across the global
    matchCompleted = False

    def __init__(self, matchID):
        self.matchID = str(matchID)