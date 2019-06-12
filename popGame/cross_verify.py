from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15
import rehash
import time, pickle

class cross_verify:

    def __init__(self, plyrData, myConf, key, gameConf, sk):
        self.plyrData = plyrData
        self.myConf = myConf
        self.gameConf = gameConf
        self.sk = sk
        self.key = key
        return

    def start(self, records):
        return self.cross_verify(records)

    def crossVerifyGameRes(self):
        # print("", self.plyrData.plyrsRes)
        # check if every signed is valid
        for receiverPID in self.plyrData.gamePlyrs:
            for senderPID in self.plyrData.gamePlyrs:
                gameResult = pickle.dumps(pickle.loads(self.plyrData.plyrsRes[receiverPID]).matchData)
                gameResHash = SHA256.new(gameResult)
                if gameResHash.hexdigest() != self.plyrData.plyrsResHash[senderPID][receiverPID].hexdigest():
                    return False
                try:
                    pkcs1_15.new(RSA.import_key(self.plyrData.plyrsPubK[receiverPID])).verify(
                        gameResHash, self.plyrData.plyrsSignRes[senderPID][receiverPID]
                    )
                    # print(self.plyrData.plyrsPubK[receiverPID], self.plyrData.plyrsRes[receiverPID], self.plyrData.plyrsSignRes[senderPID][receiverPID], "======>", True)
                except (ValueError, TypeError):
                    # print(self.plyrData.plyrsPubK[receiverPID], self.plyrData.plyrsRes[receiverPID], self.plyrData.plyrsSignRes[senderPID][receiverPID], "======>", False)
                    return False
        return True

    def consensusOnGameRes(self):
        # calculate and get the record with most consensus
        matchConsensus = {}
        # print("signRes111:", self.plyrData.plyrsSignRes)
        for basePlayerID, baseResList in self.plyrData.plyrsRes.items():
            for dump, resList in self.plyrData.plyrsRes.items():
                if baseResList == resList:
                    if basePlayerID not in matchConsensus: matchConsensus[basePlayerID] = 1
                    else: matchConsensus[basePlayerID] += 1
        count, consensusPlayerID = max((v, k) for k, v in matchConsensus.items())

        # according to the most consensus record, get the MVP
        # print("===================")
        # print(self.plyrData.plyrsRes)
        # print(consensusPlayerID)
        # print(pickle.loads(self.plyrData.plyrsRes[consensusPlayerID]))
        # print(self.plyrData.return_signature())
        # print(matchConsensus)
        # print("====================")
        consensusGameRes = pickle.loads(self.plyrData.plyrsRes[consensusPlayerID])
        # print("signRes111:", self.plyrData.plyrsSignRes)
        consensusGameRes.signature = self.plyrData.return_signature()
        self.plyrData.consensusGameRes = consensusGameRes
        MVP = consensusGameRes.returnMVP()
        if self.key.pubKey == MVP:
            print("I am the MVP {}, broadcasting data...".format(MVP))
            # self.broadcastOnGameRes(consensusGameRes)
        else:
            print("I am not the MVP, the MVP is {}".format(MVP))
        return consensusGameRes.returnMatchData(), MVP

    def broadcastGameHash(self, records):
        # print("MatchData:", records)
        if self.myConf.ID not in self.plyrData.plyrsSignRes: self.plyrData.plyrsSignRes[self.myConf.ID] = {}
        if self.myConf.ID not in self.plyrData.plyrsResHash: self.plyrData.plyrsResHash[self.myConf.ID] = {}

        self.plyrData.plyrsRes[self.myConf.ID] = pickle.dumps(records)
        matchData = pickle.dumps(records.matchData)
        gameResRehash = rehash.sha256(matchData)
        gameResHash = SHA256.new(matchData)
        signedGameResHash = pkcs1_15.new(RSA.import_key(self.key.priKey)).sign(gameResHash)
        self.plyrData.plyrsSignRes[self.myConf.ID][self.myConf.ID] = signedGameResHash
        self.plyrData.plyrsResHash[self.myConf.ID][self.myConf.ID] = gameResHash

        self.sk.sock.send({"pickleGameResRehash": pickle.dumps(gameResRehash)
            , "pickleSignedGameResHash": pickle.dumps(signedGameResHash)})
        return

    def broadcastGameRes(self):
        self.sk.sock.send({"gameRes": self.plyrData.plyrsRes[self.myConf.ID]})

    def cross_verify(self, gameRes):
        # shared turn phase 1: broadcast game hash, signedHash
        self.broadcastGameHash(gameRes)

        timerOn, curTime = time.time(), time.time()
        while curTime - timerOn < 60:
            flag = True
            # print(self.plyrData.plyrsSignRes.keys())
            for playerID in self.plyrData.plyrsSignRes:
                # print(playerID, self.plyrData.plyrsSignRes[playerID])
                if len(self.plyrData.plyrsSignRes[playerID]) != len(self.plyrData.gamePlyrs):
                    flag = False
            if flag: break
            time.sleep(1)
            curTime = time.time()
        if curTime - timerOn >= 60: return None, None
        # print("signRes:", self.plyrData.plyrsSignRes)

        # shared turn phase 2: broadcast game res, and verify
        self.broadcastGameRes()
        timerOn, curTime = time.time(), time.time()
        while curTime - timerOn < 60:
            if len(self.plyrData.plyrsRes) == len(self.plyrData.gamePlyrs): break
            time.sleep(1)
            curTime = time.time()
        if curTime - timerOn >= 60: return None, None
        matchVerified = self.crossVerifyGameRes()
        # print("signRes:", self.plyrData.plyrsSignRes)

        if not matchVerified: return None, None
        consensusGameRes, isMVP = self.consensusOnGameRes()
        self.gameConf.matchCompleted = True
        return consensusGameRes, isMVP