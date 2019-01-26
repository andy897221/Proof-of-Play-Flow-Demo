import sys, time
from threading import Thread
sys.path.insert(0, './../')
import PoP
import myGetMVP, myGetRating # function written by the user
import generator.matchGenerator as matchGen # test function to demonstrate library

# the nodeID config is already generated, please refer to sample_setup.py
nodeID = "Bob"
myPoP = PoP.handler(nodeID=nodeID, winnerFunc=myGetMVP.getMVP, ratingFunc=myGetRating.getRating)


@myPoP.run_blockchain(saveState=False, auto_broadcast=False)
def run_blockchain():
    ################ blockchain entry is running, you can execute any code here ################
    print("\nthese are the matches generated as sample, 1 block will be written: \n")
    data = matchGen.new_match(0, 1)
    myPoP._direct_send_match(data)
    data = matchGen.new_match(0, 1)
    myPoP._direct_send_match(data)
    print("\nmatches generation completed \n")

    print("\nwaiting bootstrap chain to replace our chain\n")
    while myPoP.return_chain_status()['current index'] < 3: # waiting for bootstrap blockchain replace my blockchain
        time.sleep(3)
    print("\nour chain has been replaced, but since bootstrap chain dont have our generated matches, and the rating exceeds the target, we wrote a block and now start broadcasting.\n")

    myPoP.broadcast_chain()
    print([f"{key}: {item}" for key, item in myPoP.return_chain_status().items() if key != 'pubKey'])
    myPoP.terminate()
    return

try:
    blockchain = Thread(target=run_blockchain)
    blockchain.daemon = True
    blockchain.start()
    while blockchain.isAlive(): time.sleep(1)
except (KeyboardInterrupt, SystemExit):
    print("example completed")