import sys
sys.path.insert(0, './../')
import PoP
import myGetMVP, importGameRes, myGetRating # function written by the user


# the nodeID config is already generated, please refer to sample_setup.py
nodeID, matchID = "client", 1
myPoP = PoP.handler(nodeID=nodeID, winnerFunc=myGetMVP.getMVP, ratingFunc=myGetRating.getRating)



def run_match(thisMatchID):
    @myPoP.run_conn(matchID=thisMatchID)
    def my_match():
        ########## API entry and p2p entry threads are running, you can execute any code here ##########

        # create a two player pop match
        myPoP.game_conn_to("127.0.0.1:2000") # connect to bootstrap node

        plyrList = myPoP.return_plyrList()
        # assume a match record has been produced from a match: 1533081738_4035507616_match.data
        with open('1533081738_4035507616_match.data', 'r') as f: rawGameRec = f.read()
        gamePlyrList = sorted([item for key, item in plyrList.items()]) # assume the match records corresponds to this plyr list
        gameRec = importGameRes.importGameResult(rawGameRec, gamePlyrList)

        myPoP.verify_game(gameRec)
        res = myPoP.broadcast_gameRec()
        print(res)

        myPoP.terminate() # pop will only be terminated if this is ran, otherwise it freeze at the end of this function
        return
    my_match()



if __name__ == '__main__':
    try:
        run_match(thisMatchID=matchID)
    except (KeyboardInterrupt, SystemExit):
        print("example completed")