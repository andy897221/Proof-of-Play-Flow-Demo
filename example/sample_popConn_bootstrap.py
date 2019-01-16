import argparse
import PoP

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--nodeID", type=str, help="your node ID")
args =parser.parse_args()

def main(nodeID):
    # a way to warn PoP_init
    # google: know the directory path of the function caller
    from_path = "C:/Users/andy8/Desktop/Proof-of-Play/example"
    setupJSON = {
        "nodeID": str(nodeID),
        "game_port": "1000",
        "blockchain_port": "1001",
        "API_port": "1002",
        "blockchain_bootstrap_ip": None,
        "keyLoc": "./config/nodeKey",
        "blockchainLoc": "./popBlockchain/data",
    }
    popObject = PoP.handler(from_path=from_path, nodeID=nodeID, setupJSON=setupJSON)
    popObject.run_conn()
