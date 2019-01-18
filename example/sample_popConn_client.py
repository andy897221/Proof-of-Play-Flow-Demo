import sys
sys.path.insert(0, './../')
import PoP
# your function
import myGetMVP, importGameRes

# the nodeID config is already generated, please refer to sample_setup.py
nodeID, matchID = "Bob", 1
myPoP = PoP.handler(nodeID=nodeID, winnerFunc=myGetMVP.getMVP)

@myPoP.run_conn(matchID=matchID)
def main():
    ########## API entry and p2p entry threads are running, you can execute any code here ##########

    # create a two player pop match
    res = myPoP.game_conn_to("127.0.0.1:1000") # connect to bootstrap node
    print(res)

    plyrList = myPoP.return_plyrList()
    # assume a match record has been produced from a match: 1533081738_4035507616_match.data
    with open('1533081738_4035507616_match.data', 'r') as f: rawGameRec = f.read()
    gamePlyrList = sorted([item for key, item in plyrList.item()]) # assume the match records corresponds to this plyr list
    gameRec = importGameRes.importGameResult(rawGameRec, gamePlyrList)

    myPoP.verify_game(gameRec)
    return

main()