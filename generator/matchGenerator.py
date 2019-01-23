import popGame.helper
import example.myGetMVP as myGetMVP
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15
from Crypto.PublicKey import RSA
import pickle

Alice_Bob_keyFolder = "./../example/config"

with open(Alice_Bob_keyFolder+"/Alice.pubKey", "rb") as f:
    AlicePubKey = f.read()
with open(Alice_Bob_keyFolder+"/Bob.pubKey", "rb") as f:
    BobPubKey = f.read()
with open(Alice_Bob_keyFolder+"/Alice.priKey", "rb") as f:
    AlicePriKey = f.read()
with open(Alice_Bob_keyFolder+"/Bob.priKey", "rb") as f:
    BobPriKey = f.read()

def main(AliceRating, BobRating):
    # change all enum rating to be same because it doesnt matter which param is the rating
    enum = ["gold_per_min", "xp_per_min", "kills_per_min", "last_hits_per_min", "hero_damage_per_min",
                "hero_healing_per_min", "tower_damage", "stuns_per_min"]

    plyrAddrList = [AlicePubKey, BobPubKey]

    matchData = {AlicePubKey: {}, BobPubKey: {}}
    for i in enum:
        matchData[AlicePubKey][i] = AliceRating/(AliceRating+BobRating)
        matchData[BobPubKey][i] = BobRating/(AliceRating+BobRating)
    matchData = popGame.helper.plyrResList(matchData=matchData, winnerFunc=myGetMVP.getMVP, pubKeyList=plyrAddrList)

    if AliceRating > BobRating: winnerAddr = AlicePubKey
    else: winnerAddr = BobPubKey

    aliceSigned = pkcs1_15.new(RSA.import_key(AlicePriKey)).sign(SHA256.new(pickle.dumps(matchData)))
    bobSigned = pkcs1_15.new(RSA.import_key(BobPriKey)).sign(SHA256.new(pickle.dumps(matchData)))
    signature = {AlicePubKey: {AlicePubKey: aliceSigned, BobPubKey: bobSigned}, BobPubKey: {AlicePubKey: aliceSigned, BobPubKey: bobSigned}}

    data = {'plyrAddrList': plyrAddrList, 'winnerAddr': winnerAddr, 'matchData': matchData, 'signature': signature}