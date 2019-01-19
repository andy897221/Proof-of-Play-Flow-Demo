import sys
sys.path.insert(0, './../')
import PoP
import myGetMVP, importGameRes # function written by the user

# the nodeID config is already generated, please refer to sample_setup.py
nodeID, matchID = "Bob", 1
myPoP = PoP.handler(nodeID=nodeID, winnerFunc=myGetMVP.getMVP)

def main(thisMatchID):

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

        gameRec, isMVP = myPoP.verify_game(gameRec)
        print(gameRec, isMVP)

        myPoP.terminate() # pop will only be terminated if this is ran, otherwise it freeze at the end of this function
        return

    my_match()

main(thisMatchID=matchID)