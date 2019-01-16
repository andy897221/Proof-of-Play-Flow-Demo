import argparse
import PoP

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--nodeID", type=str, help="your node ID")
parser.add_argument("-p", "--fromPath", type=str, help="pop config path")
args =parser.parse_args()

def main(nodeID, from_path):
    popObject = PoP.handler(from_path=from_path, nodeID=nodeID)

main(args.nodeID, args.fromPath)