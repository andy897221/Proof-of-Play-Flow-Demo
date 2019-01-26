import json, os
from Crypto.PublicKey import RSA

def init_key(from_path, param_json):
        print(
            "public and private key file based on the nodeID is not found, generating public and private key files...")
        key = RSA.generate(2048)

        with open(f"{from_path}/{param_json['keyLoc']}/{param_json['nodeID']}.pubKey", 'wb') as pubKeyF:
            pubKeyF.write(key.publickey().export_key())
        with open(f"{from_path}/{param_json['keyLoc']}/{param_json['nodeID']}.priKey", 'wb') as priKeyF:
            priKeyF.write(key.export_key())
        print("generation completed.")
        return

def init(from_path, nodeID=1, setupJSON=None):
    isDefault = True
    setup_frame = {
        "nodeID": str(nodeID),
        "game_port": 1000,
        "blockchain_port": 1001,
        "API_port": 1002,
        "blockchain_bootstrap_ip": None,
        "keyLoc": "./config/nodeKey",
        "blockchainLoc": "./config/blockchain",
    }
    if setupJSON is None:
        print("input the value and press enter, press enter directly to use the default value:")
        setup_frame["nodeID"] = input(f"your node id / name (default - '{setup_frame['nodeID']}'): ") or setup_frame['nodeID']
        setup_frame["game_port"] = input(f"your port (default - {setup_frame['game_port']}): ") or setup_frame['game_port']
        setup_frame['blockchain_port'] = input(f"your blockchain port (default - '{setup_frame['blockchain_port']}'): ") or setup_frame['blockchain_port']
        setup_frame['API_port'] = input(f"your API port address for hosting p2p (default - '{setup_frame['API_port']}'): ") or setup_frame['API_port']
        setup_frame['blockchain_bootstrap_ip'] = input(f"your blockchain bootstrap ip (default - '{setup_frame['blockchain_bootstrap_ip']}'): ") or setup_frame['blockchain_bootstrap_ip']
        setup_frame['keyLoc'] = input(f"your public and private key directory (default - '{setup_frame['keyLoc']}'): ") or setup_frame['keyLoc']
        setup_frame['blockchainLoc'] = input(f"your .blockchain file and other related blockchain files directory (default - {setup_frame['blockchainLoc']}): ") or setup_frame['blockchainLoc']
    else:
        isDefault = False
        for key, item in setupJSON.items():
            setup_frame[key] = setupJSON[key]

    if not os.path.exists(f"{from_path}/config") and isDefault: os.makedirs(f"{from_path}/config")
    if not os.path.exists(f"{from_path}/config/nodeKey") and isDefault: os.makedirs(f"{from_path}/config/nodeKey")
    if not os.path.exists(f"{from_path}/config/blockchain") and isDefault: os.makedirs(f"{from_path}/config/blockchain")
    if (not os.path.isfile(f"{from_path}/{setup_frame['keyLoc']}/{setup_frame['nodeID']}.pubKey") or not os.path.isfile(
            f"{from_path}/{setup_frame['keyLoc']}/{setup_frame['nodeID']}.priKey")) and isDefault: init_key(from_path, setup_frame)
    with open(f"./config/{setup_frame['nodeID']}.json", "w") as f:
        f.write(json.dumps(setup_frame))
    print("config initialization completed.")