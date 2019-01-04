import os, json
import numpy as np
from Crypto.PublicKey import RSA

# def init_keyPair(pubKeyFile, priKeyFile):
#     key = RSA.generate(2048)
#     priKey = key.export_key()
#     pubKey = key.publickey().export_key()
#     with open(f"{pubKeyFile}", "wb") as pubKeyF:
#         pubKeyF.write(key.publickey().export_key())
#     with open(f"{priKeyFile}", "wb") as priKeyF:
#         priKeyF.write(key.export_key())
#     return pubKey, priKey

def init_keyPair(pubKeyFile, priKeyFile):
    if not os.path.isfile(f"{pubKeyFile}") or not os.path.isfile(f"{priKeyFile}"):
        print(f"{pubKeyFile} no key pair found, generating new private and public key for node ID.")
        key = RSA.generate(2048)
        priKey = key.export_key()
        pubKey = key.publickey().export_key()
        with open(f"{pubKeyFile}", "wb") as pubKeyF:
            pubKeyF.write(key.publickey().export_key())
        with open(f"{priKeyFile}", "wb") as priKeyF:
            priKeyF.write(key.export_key())
    else:
        print(f"{pubKeyFile} key pair found, reading existing private and public key for node ID.")
        with open(f"{pubKeyFile}", "rb") as pubKeyF:
            pubKey = pubKeyF.read()
        with open(f"{priKeyFile}", "rb") as priKeyF:
            priKey = priKeyF.read()
    return pubKey, priKey

def importGameResult(match):
    with open(f"{match}", "r") as f:
        content = f.read()
    content = json.loads(content)

    matchData = []
    radiantWins = content["radiant_win"]
    enum = ["gold_per_min", "xp_per_min", "kills_per_min", "last_hits_per_min", "hero_damage_per_min", "hero_healing_per_min", "tower_damage", "stuns_per_min"]
    for i in range(0, len(content["players"])):
        matchData += [{}]
        for j in enum:
            matchData[i][j] = content["players"][i]["benchmarks"][j]["raw"]
        matchData[i]["isRadiant"] = content["players"][i]["isRadiant"]

    mvpIndex, mvpType = getMVP(matchData, radiantWins)
    return matchData, mvpIndex

def getMVP(matchData, radiantWins):
    # use highest parameter based total parameter values of all players
    enum = ["gold_per_min", "xp_per_min", "kills_per_min", "last_hits_per_min", "hero_damage_per_min", "hero_healing_per_min", "tower_damage", "stuns_per_min"]
    plyrRating, ratingBase = {"param": [], "rating": []}, []

    for i in range(0, len(matchData)):
        ratingBase += [[matchData[i][j] for j in enum]]
    ratingBase = list(np.asarray(ratingBase).sum(axis=0))
    
    for i in range(0, len(matchData)):
        plyrallParam = [(matchData[i][enum[j]] / ratingBase[j]) if ratingBase[j] != 0 else 0 for j in range(0, len(enum))]
        plyrRating["param"] += [enum[np.argmax(plyrallParam)]]
        plyrRating["rating"] += [max(plyrallParam)]
    plyrRating_np = np.asarray(plyrRating["rating"])

    plyrWins = []
    for i in range(0,len(matchData)):
        if matchData[i]["isRadiant"] and radiantWins: plyrWins += [True]
        elif matchData[i]["isRadiant"] and not radiantWins: plyrWins += [False]
        elif not matchData[i]["isRadiant"] and radiantWins: plyrWins += [False]
        elif not matchData[i]["isRadiant"] and not radiantWins: plyrWins += [True]
    plyrWins = np.asarray(plyrWins)
    
    mvpIndex = np.where(plyrWins == True)[0][np.argmax(plyrRating_np[plyrWins])]
    return mvpIndex, plyrRating["param"][mvpIndex]

#parse matches
matches = []
matchToPlyrNode = []
nodePubKey = []
nodePriKey = []

print("initializing matches...")
for f in os.listdir("./genesis_matches"):
    matches += ["./genesis_matches/{}".format(f)]

# define 50 players, use array with init value 0, nodeID 1 to 50, for loop 500 records, get necessary json for the blockchain and write into a file

# after generation, in blockchain, calculate target of a player according to .txt and previous block (this gensis block)

for match in range(0,len(matches)):
    startPlyr = (match % 5) * 10
    matchToPlyrNode += [[i for i in range(startPlyr, startPlyr+10)]]

print("generating public / private key...")
for node in range(0, 50):
    pubKey, priKey = init_keyPair(f"./nodeKey/{node+1}.pubKey", f"./nodeKey/{node+1}.priKey")
    nodePubKey += [pubKey]
    nodePriKey += [priKey]

print("generating matches...")
for match in range(0,len(matches)):
    sortedPubKey = [nodePubKey[matchToPlyrNode[match][i]].decode("utf-8") for i in range(0, 10)]
    matchData, mvpIndex = importGameResult(matches[match])
    winnerAddr = sortedPubKey[mvpIndex]
    with open("genesis_block.data", "a+") as f:
        f.write("{},".format(
            json.dumps({'plyrAddrList': sortedPubKey, 'winnerAddr': winnerAddr, 'matchData': matchData})))
        print(json.dumps({'plyrAddrList': sortedPubKey, 'winnerAddr': winnerAddr, 'matchData': matchData}))