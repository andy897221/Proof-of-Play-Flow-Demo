import sys, time
from threading import Thread
sys.path.insert(0, './../')
import PoP
import myGetMVP, myGetRating # function written by the user
import generator.matchGenerator as matchGen # test function to demonstrate library

# the nodeID config is already generated, please refer to sample_setup.py
nodeID = "Alice"
myPoP = PoP.handler(nodeID=nodeID, winnerFunc=myGetMVP.getMVP, ratingFunc=myGetRating.getRating)


@myPoP.run_blockchain(saveState=False, auto_broadcast=False)
def run_blockchain():
    ################ blockchain entry is running, you can execute any code here ################
    while True:
        nodes = myPoP.return_node()
        addr = [item for key, item in nodes.items()]
        if "127.0.0.1:1004" in addr: break
        time.sleep(5)

    print("\nthese are the matches generated as sample, 2 blocks will be written: \n")
    data = matchGen.new_match(1, 0)
    myPoP._direct_send_match(data)
    data = matchGen.new_match(10, 0)
    myPoP._direct_send_match(data)
    data = matchGen.new_match(1, 0)
    myPoP._direct_send_match(data)
    data = matchGen.new_match(10, 0)
    myPoP._direct_send_match(data)
    data = matchGen.new_match(10, 0)
    myPoP._direct_send_match(data)
    print("\nmatches generation completed \n")

    time.sleep(5) # waiting for client blockchain writing matches
    print("\nour chain will then be broadcasted, client will generate some matches afterwards and exceed our chain length \n")
    myPoP.broadcast_chain()
    print("\nwaiting client replaces our chain... \n")

    while myPoP.return_chain_status()['current index'] < 4: # waiting for client blockchain replace my blockchain
        time.sleep(3)
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