import sys, time
from threading import Thread
sys.path.insert(0, './../')
import PoP
import myGetMVP, importGameRes, myGetRating # function written by the user

# the nodeID config is already generated, please refer to sample_setup.py
nodeID, matchID = "Alice", 1
myPoP = PoP.handler(nodeID=nodeID, winnerFunc=myGetMVP.getMVP, ratingFunc=myGetRating.getRating)



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

        myPoP.verify_game(gameRec) # this will reutrn (gameRec, MVP) for user operations if required
        myPoP.broadcast_gameRec()

        myPoP.terminate() # pop will only be terminated if this is ran, otherwise it freeze at the end of this function
        return
    this_match()



waitingMatch = True
@myPoP.run_blockchain(saveState=False)
def run_blockchain():
    ################ blockchain entry is running, you can execute any code here ################
    print("blockchain is running")
    while waitingMatch: time.sleep(1)
    print(myPoP.return_chain_status())
    myPoP.terminate()



if __name__ == '__main__':
    try:
        blockchain = Thread(target=run_blockchain)
        blockchain.daemon = True
        blockchain.start()
        run_match(thisMatchID=matchID)
        time.sleep(1)
        waitingMatch = False
        while blockchain.isAlive(): time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        print("example completed")