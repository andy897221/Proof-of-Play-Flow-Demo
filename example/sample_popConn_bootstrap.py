import sys, time
sys.path.insert(0, './../')
import PoP
import myGetMVP, importGameRes # function written by the user

# the nodeID config is already generated, please refer to sample_setup.py
nodeID, matchID = "Alice", 1
myPoP = PoP.handler(nodeID=nodeID, winnerFunc=myGetMVP.getMVP)

def run_match(thisMatchID):

    @myPoP.run_conn(matchID=thisMatchID)
    def this_match():
        ########## API entry and p2p entry threads are running, you can execute any code here ##########

        while len(myPoP.return_plyrList()) < 2: time.sleep(1)
        plyrList = myPoP.return_plyrList()

        # assume a match record has been produced from a match: 1533081738_4035507616_match.data
        with open('1533081738_4035507616_match.data', 'r') as f: rawGameRec = f.read()
        gamePlyrList = sorted([item for key, item in plyrList.items()])  # assume the match records sorted corresponds to this plyr list
        gameRec = importGameRes.importGameResult(rawGameRec, gamePlyrList)

        gameRec, isMVP = myPoP.verify_game(gameRec)
        print(gameRec, isMVP)

        myPoP.terminate() # pop will only be terminated if this is ran, otherwise it freeze at the end of this function
        return

    this_match()

# run blockchain
run_match(thisMatchID=matchID)
# run_match(thisMatchID=matchID)
# run_match(thisMatchID=matchID)
# run_match(thisMatchID=matchID)
# ...
# check blockchain data existence and verify (e.g. target exists)
# manually edit target value, check basic blockchain operation (write block)