import json, os
from Crypto.PublicKey import RSA

def init(from_path, nodeID=1, setupJSON=None):
    if setupJSON is None:
        param_json = {
            "nodeID": str(nodeID),
            "game_port": "1000",
            "blockchain_port": "1001",
            "API_port": "1002",
            "blockchain_bootstrap_ip": None,
            "keyLoc": "./config/nodeKey",
            "blockchainLoc": "./popBlockchain/data",
        }
        print("input the value and press enter, press enter directly to use the default value:")

        param_json["nodeID"] = input(f"your node id / name (default - '{param_json['nodeID']}'): ") or param_json['nodeID']

        param_json["game_port"] = input(f"your port (default - {param_json['game_port']}): ") or param_json['game_port']

        param_json['blockchain_port'] = input(f"your blockchain port (default - '{param_json['blockchain_port']}'): ") or param_json['blockchain_port']

        param_json['API_port'] = input(f"your API port address for hosting p2p (default - '{param_json['API_port']}'): ") or param_json['API_port']

        param_json['blockchain_bootstrap_ip'] = input(f"your blockchain bootstrap ip (default - '{param_json['blockchain_bootstrap_ip']}'): ") or param_json['blockchain_bootstrap_ip']

        param_json['keyLoc'] = input(f"your public and private key directory (default - '{param_json['keyLoc']}'): ") or param_json['keyLoc']
        if not os.path.isfile(param_json['keyLoc']+"/"+param_json['nodeID']+".priKey") or not os.path.isfile(param_json['keyLoc']+"/"+param_json['nodeID']+".priKey"):
            print("public and private key file based on the nodeID is not found, generating public and private key files...")
            key = RSA.generate(2048)
            with open(f"{param_json['keyLoc']}/{param_json['nodeID']}.pubKey", 'wb') as pubKeyF:
                pubKeyF.write(key.publickey().export_key())
            with open(f"{param_json['keyLoc']}/{param_json['nodeID']}.priKey", 'wb') as priKeyF:
                priKeyF.write(key.export_key())
            print("generation completed.")

        param_json['blockchainLoc'] = input(f"your .blockchain file and other related blockchain files directory (default - {param_json['blockchainLoc']}): ") or param_json['blockchainLoc']
    else:
        param_json = setupJSON

    os.makedirs(f"{from_path}/config")
    with open(f"./config/{param_json['nodeID']}.json", "w") as f:
        f.write(json.dumps(param_json))
    print("config initialization completed.")