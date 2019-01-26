import os, json
import numpy as np
from Crypto.PublicKey import RSA
import argparse
import pickle

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config", type=str, help="existing config folder location")
args = parser.parse_args()

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

def importGameResult(content, plyrList):
    # format the matchData as such:
    # matchData[0] = {"plyrPubKey": {"gold_per_min", "xp_per_min", "kills_per_min", "last_hits_per_min", "hero_damage_per_min", "hero_healing_per_min", "tower_damage", "stuns_per_min", "isRadiant"}}
    # first item of matchData is a dictionary of rating dictionary of a player
    # second item of matchData is radiantWins, a boolean value
    content = json.loads(content)
    matchData = dict()
    radiantWins = content["radiant_win"]
    enum = ["gold_per_min", "xp_per_min", "kills_per_min", "last_hits_per_min", "hero_damage_per_min", "hero_healing_per_min", "tower_damage", "stuns_per_min"]

    # if len(plyrList) != len(content["players"]): return False
    plyrList = [plyr for plyr in plyrList]
    for plyr in range(0, len(plyrList)):
        matchData[plyrList[plyr]] = {}
        for j in enum:
            matchData[plyrList[plyr]][j] = content["players"][plyr]["benchmarks"][j]["raw"]
        if plyr == 0: matchData[plyrList[plyr]]["isRadiant"] = True
        else: matchData[plyrList[plyr]]["isRadiant"] = False

    matchData = [matchData, radiantWins]

    return matchData, getMVP(matchData)

def getMVP(matchData):
    """
    use highest parameter based total parameter values of all players
    :param matchData: any data type to process by your function
    :return: int, index of player list
    """

    enum = ["gold_per_min", "xp_per_min", "kills_per_min", "last_hits_per_min", "hero_damage_per_min",
            "hero_healing_per_min", "tower_damage", "stuns_per_min"]
    plyrRating, ratingBase = {"param": [], "rating": []}, []
    team1Wins = matchData[1]
    matchData = matchData[0]

    for key, item in matchData.items():
        ratingBase += [[matchData[key][j] for j in enum]]
    ratingBase = list(np.asarray(ratingBase).sum(axis=0))

    for key, item in matchData.items():
        plyrallParam = [(matchData[key][enum[j]] / ratingBase[j]) if ratingBase[j] != 0 else 0 for j in
                        range(0, len(enum))]
        plyrRating["param"] += [enum[int(np.argmax(plyrallParam))]]
        plyrRating["rating"] += [max(plyrallParam)]
    plyrRating_np = np.asarray(plyrRating["rating"])

    plyrWins = []
    for key, item in matchData.items():
        if matchData[key]["isRadiant"] and team1Wins: plyrWins += [True]
        elif matchData[key]["isRadiant"] and not team1Wins: plyrWins += [False]
        elif not matchData[key]["isRadiant"] and team1Wins: plyrWins += [False]
        elif not matchData[key]["isRadiant"] and not team1Wins: plyrWins += [True]
    plyrWins = np.asarray(plyrWins)

    mvpIndex = np.where(plyrWins == True)[0][np.argmax(plyrRating_np[plyrWins])]
    return int(mvpIndex)

#parse matches
matches = []
matchToPlyrNode = []
nodePubKey = []
nodePriKey = []

print("initializing matches...")
for f in os.listdir("./../resources/genesis_matches"):
    matches += ["./../resources/genesis_matches/{}".format(f)]

# define 50 players, use array with init value 0, nodeID 1 to 50, for loop 500 records, get necessary json for the blockchain and write into a file

# after generation, in blockchain, calculate target of a player according to .txt and previous block (this gensis block)

for match in range(0,len(matches)):
    startPlyr = (match % 5) * 10
    matchToPlyrNode += [[i for i in range(startPlyr, startPlyr+10)]]


config = args.config+"/nodeKey"
existingPubKey = [config+"/"+pubKey for pubKey in os.listdir(config) if ".pubKey" in pubKey]
existingPriKey = [config+"/"+priKey for priKey in os.listdir(config) if ".priKey" in priKey]
for node in range(0, len(existingPubKey)):
    with open(existingPubKey[node], "rb") as pubKey:
        nodePubKey += [pubKey.read()]
    with open(existingPriKey[node], "rb") as priKey:
        nodePriKey += [priKey.read()]

print("generating public / private key...")
if not os.path.exists("./config"): os.makedirs("./config")
if not os.path.exists("./config/nodeKey"): os.makedirs("./config/nodeKey")
for node in range(0, 50-len(existingPubKey)):
    pubKey, priKey = init_keyPair(f"./config/nodeKey/{node+1}.pubKey", f"./config/nodeKey/{node+1}.priKey")
    nodePubKey += [pubKey]
    nodePriKey += [priKey]

print("generating matches...")
data = []
for match in range(0,len(matches)):
    sortedPubKey = [nodePubKey[matchToPlyrNode[match][i]] for i in range(0, 10)]
    with open(matches[match]) as f:
        matchData, mvpIndex = importGameResult(f.read(), sortedPubKey)
    winnerAddr = sortedPubKey[mvpIndex]
    data.append({'plyrAddrList': sortedPubKey, 'winnerAddr': winnerAddr, 'matchData': matchData})
with open("genesis_block.data", "wb") as f:
    f.write(pickle.dumps(data))