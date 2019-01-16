from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15
import rehash
import time, pickle

import requests

class cross_verify:

    def __init__(self, plyrData, myConf, sk, config, blockchain_port):
        self.plyrData = plyrData
        self.myConf = myConf
        self.gameConf = config.gameConf
        self.sk = sk
        self.key = config.key
        self.blockchain_port = blockchain_port
        return

    def start(self, records):
        print(self.cross_verify(records)[0])
        return

    def crossVerifyGameRes(self):
        # check if every signed is valid
        for receiverPID in self.plyrData.plyrsPubK:
            for senderPID in self.plyrData.plyrsPubK:
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

    def broadcastOnGameRes(self, consensusGameRes):
        sortedPubKey = [self.plyrData.plyrsPubK[i].decode("utf-8") for i in self.plyrData.gamePlyrs]
        res =  requests.post(f'http://{self.blockchain_port}/matches/new'
                    , json={'plyrAddrList': sortedPubKey, 'winnerAddr': self.plyrData.plyrsPubK[consensusGameRes.returnMVP(self.plyrData)].decode("utf-8"), 'matchData': consensusGameRes.returnDict()})
        print(res.text)
        return

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
        MVP = consensusGameRes.returnMVP(self.plyrData)
        if self.myConf.ID == MVP:
            print("I am the MVP {}, broadcasting data...".format(MVP))
            self.broadcastOnGameRes(consensusGameRes)
        else:
            print("I am not the MVP, the MVP is {}".format(MVP))
        return

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
            for playerID in gameRes.plyrsSignRes:
                if len(gameRes.plyrsSignRes[playerID]) != len(self.plyrData.gamePlyrs):
                    flag = False
            if flag: break
            time.sleep(1)
            curTime = time.time()
        if curTime - timerOn >= 60: return "shared turn time out", False

        # shared turn phase 2: broadcast game res, and verify
        self.broadcastGameRes()
        timerOn, curTime = time.time(), time.time()
        while curTime - timerOn < 60:
            if len(gameRes.plyrsRes) == len(self.plyrData.gamePlyrs): break
            time.sleep(1)
            curTime = time.time()
        if curTime - timerOn >= 60: return "shared turn time out", False
        matchVerified = self.crossVerifyGameRes()

        if not matchVerified: return "match verification failed", False
        self.consensusOnGameRes()
        self.gameConf.matchCompleted = True
        return "match verification and consensus succeeded", True