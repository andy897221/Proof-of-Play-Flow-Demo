import pickle, time

class sock:
    sock = ""  # socket for connect nodes, send ,recv msg

    def __init__(self, myConf, gameConf, key, plyrData):
        self.myConf = myConf
        self.gameConf = gameConf
        self.key = key
        self.plyrData = plyrData

    def readHandler(self):
        while True:
            if self.gameConf.matchCompleted: break

            msg = self.sock.recv()
            if msg is not None:
                decodedMsg = msg.packets[1]
                if "handshaking" in decodedMsg and "matchID" in decodedMsg and "pubKey" in decodedMsg:
                    if self.gameConf.gameOn:
                        print("match is full".format(str(msg.sender)))
                        msg.reply({"gameOn": 1})
                    else:
                        if decodedMsg["matchID"] == self.gameConf.matchID and msg.sender not in self.plyrData.gamePlyrs:
                            pubKey = pickle.loads(decodedMsg["pubKey"])
                            self.plyrData.add_gamePlyrs(msg.sender)
                            self.plyrData.plyrsPubK[msg.sender] = pubKey
                        print("connection from player "+str(msg.sender)+", match ID: "+decodedMsg["matchID"])
                        msg.reply({"ack": 1, "matchID": self.gameConf.matchID, "pubKey": pickle.dumps(self.key.pubKey)})

                if "ack" in decodedMsg and "matchID" in decodedMsg and "pubKey" in decodedMsg:
                    if decodedMsg["matchID"] == self.gameConf.matchID and msg.sender not in self.plyrData.gamePlyrs:
                        pubKey = pickle.loads(decodedMsg["pubKey"])
                        self.plyrData.add_gamePlyrs(msg.sender)
                        self.plyrData.plyrsPubK[msg.sender] = pubKey
                    print("connection established with player "+str(msg.sender)+"match ID: "+decodedMsg["matchID"])

                if "pickleSignedGameResHash" in decodedMsg and "exchangeSignedGameResHash" not in decodedMsg:
                    signedGameResHash = pickle.loads(decodedMsg["pickleSignedGameResHash"])
                    gameResRehash = pickle.loads(decodedMsg["pickleGameResRehash"])

                    print("received signed game result hash from player {}".format(str(msg.sender)[0:10]+"..."))
                    if self.myConf.ID not in self.plyrData.plyrsSignRes: self.plyrData.plyrsSignRes[self.myConf.ID] = {}
                    if self.myConf.ID not in self.plyrData.plyrsResHash: self.plyrData.plyrsResHash[self.myConf.ID] = {}
                    if msg.sender not in self.plyrData.plyrsSignRes: self.plyrData.plyrsSignRes[msg.sender] = {}
                    if msg.sender not in self.plyrData.plyrsResHash: self.plyrData.plyrsResHash[msg.sender] = {}

                    self.plyrData.plyrsSignRes[self.myConf.ID][msg.sender] = signedGameResHash
                    self.plyrData.plyrsResHash[self.myConf.ID][msg.sender] = gameResRehash
                    self.plyrData.plyrsSignRes[msg.sender][msg.sender] = signedGameResHash
                    self.plyrData.plyrsResHash[msg.sender][msg.sender] = gameResRehash

                    self.sock.send({"pickleGameResRehash": decodedMsg["pickleGameResRehash"], "exchangeSignedGameResHash": 1, "playerID": msg.sender
                    , "pickleSignedGameResHash": decodedMsg["pickleSignedGameResHash"]})

                if "exchangeSignedGameResHash" in decodedMsg:
                    signedGameResHash = pickle.loads(decodedMsg["pickleSignedGameResHash"])
                    gameResRehash = pickle.loads(decodedMsg["pickleGameResRehash"])

                    print("received cross-validating signed game result hash of player {} from player {}".format(str(decodedMsg["playerID"])[0:10]+"...", str(msg.sender)[0:10]+"..."))
                    if msg.sender not in self.plyrData.plyrsSignRes: self.plyrData.plyrsSignRes[msg.sender] = {}
                    if msg.sender not in self.plyrData.plyrsResHash: self.plyrData.plyrsResHash[msg.sender] = {}
                    self.plyrData.plyrsSignRes[msg.sender][decodedMsg["playerID"]] = signedGameResHash
                    self.plyrData.plyrsResHash[msg.sender][decodedMsg["playerID"]] = gameResRehash

                if "gameRes" in decodedMsg:
                    print("received game res from player "+str(msg.sender)[0:10]+"...")
                    self.plyrData.plyrsRes[msg.sender] = decodedMsg["gameRes"]

                if "msg" in decodedMsg:
                    print(decodedMsg["msg"])

            time.sleep(1)
        return