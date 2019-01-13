# namespace
class config:
    def __init__(self, args):
        self.gameID = args.matchID
        self.port = 0 # my port for opening connection
        self.bootstrapPort = 0 # port of bootstrap node that accept connection
        self.ID = "" # my addr ID
        self.nodeID = args.nodeID
        self.APIPort = args.APIPort

class key:
    priKey = ""
    pubKey = ""

class gameConf:
    gameOn = False # lock adding players across the global
    matchCompleted = False