import sys, time
from threading import Thread
sys.path.insert(0, './../')
import PoP
import myGetMVP, importGameRes, myGetRating # function written by the user

# the nodeID config is already generated, please refer to sample_setup.py
nodeID, matchID = "Bob", 1
myPoP = PoP.handler(nodeID=nodeID, winnerFunc=myGetMVP.getMVP)

def run_match(thisMatchID):

    @myPoP.run_conn(matchID=thisMatchID)
    def my_match():
        ########## API entry and p2p entry threads are running, you can execute any code here ##########

        # create a two player pop match
        myPoP.game_conn_to("127.0.0.1:1000") # connect to bootstrap node

        plyrList = myPoP.return_plyrList()
        # assume a match record has been produced from a match: 1533081738_4035507616_match.data
        with open('1533081738_4035507616_match.data', 'r') as f: rawGameRec = f.read()
        gamePlyrList = sorted([item for key, item in plyrList.items()]) # assume the match records corresponds to this plyr list
        gameRec = importGameRes.importGameResult(rawGameRec, gamePlyrList)

        gameRec, MVP = myPoP.verify_game(gameRec)
        # verify_game use the winnerFunc supplied at object initialization of myPoP, the return must be the pub key of the winner

        myPoP.terminate() # pop will only be terminated if this is ran, otherwise it freeze at the end of this function
        return

    my_match()

@myPoP.run_blockchain(saveState=True, rating_func=myGetRating.getRating)
def run_blockchain():
    ################ blockchain entry is running, you can execute any code here ################
    while True:
        print(myPoP.return_chain_status())
        time.sleep(5)

try:
    # blockchain = Thread(target=run_blockchain)
    # blockchain.daemon = True
    # blockchain.start()
    run_match(thisMatchID=matchID)
except (KeyboardInterrupt, SystemExit):
    print("example completed")