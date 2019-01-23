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
        # check if every signed is valid
        for receiverPID in self.plyrData.gamePlyrs:
            for senderPID in self.plyrData.gamePlyrs:
                gameResHash = SHA256.new(self.plyrData.plyrsRes[receiverPID])
                if gameResHash.hexdigest() != self.plyrData.plyrsResHash[senderPID][receiverPID].hexdigest():
                    return False
                try:
                    pkcs1_15.new(RSA.import_key(self.plyrData.plyrsPubK[receiverPID])).verify(
                        gameResHash, self.plyrData.plyrsSignRes[senderPID][receiverPID]
                    )
                except (ValueError, TypeError):
                    return False
        return True

    def consensusOnGameRes(self):
        # calculate and get the record with most consensus
        matchConsensus = {}
        for basePlayerID, baseResList in self.plyrData.plyrsRes.items():
            for dump, resList in self.plyrData.plyrsRes.items():
                if baseResList == resList:
                    if basePlayerID not in matchConsensus: matchConsensus[basePlayerID] = 1
                    else: matchConsensus[basePlayerID] += 1
        count, consensusPlayerID = max((v, k) for k, v in matchConsensus.items())

        # according to the most consensus record, get the MVP
        consensusGameRes = pickle.loads(self.plyrData.plyrsRes[consensusPlayerID])
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
        if self.myConf.ID not in self.plyrData.plyrsSignRes: self.plyrData.plyrsSignRes[self.myConf.ID] = {}
        if self.myConf.ID not in self.plyrData.plyrsResHash: self.plyrData.plyrsResHash[self.myConf.ID] = {}

        self.plyrData.plyrsRes[self.myConf.ID] = pickle.dumps(records)
        gameResRehash = rehash.sha256(self.plyrData.plyrsRes[self.myConf.ID])
        gameResHash = SHA256.new(self.plyrData.plyrsRes[self.myConf.ID])
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
            for playerID in self.plyrData.plyrsSignRes:
                if len(self.plyrData.plyrsSignRes[playerID]) != len(self.plyrData.gamePlyrs):
                    flag = False
            if flag: break
            time.sleep(1)
            curTime = time.time()
        if curTime - timerOn >= 60: return None, None

        # shared turn phase 2: broadcast game res, and verify
        self.broadcastGameRes()
        timerOn, curTime = time.time(), time.time()
        while curTime - timerOn < 60:
            if len(self.plyrData.plyrsRes) == len(self.plyrData.gamePlyrs): break
            time.sleep(1)
            curTime = time.time()
        if curTime - timerOn >= 60: return None, None
        matchVerified = self.crossVerifyGameRes()

        if not matchVerified: return None, None
        consensusGameRes, isMVP = self.consensusOnGameRes()
        self.gameConf.matchCompleted = True
        return consensusGameRes, isMVP