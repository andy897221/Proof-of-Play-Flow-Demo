import json

param_json = {
    "nodeID": 1,
    "game_port": 1000,
    "blockchain_addr": "0:0:0:0:1001",
    "bootstrap_ip": None,
    "keyLoc": "./config/nodeKey",
    "blockchainLoc": "./popBlockchain/data",
}
print("input the value and press enter, press enter directly to use the default value:")

param_json["nodeID"] = input(f"your node id / name (default - '{param_json['nodeID']}'): ") or param_json['nodeID']

param_json["game_port"] = input(f"your port (default - {param_json['game_port']}): ") or param_json['game_port']

param_json['blockchain_addr'] = input(f"your blockchain address (default - '{param_json['blockchain_addr']}'): ") or param_json['blockchain_addr']

param_json['bootstrap_ip'] = input(f"your bootstrap ip (default - '{param_json['bootstrap_ip']}'): ") or param_json['bootstrap_ip']

param_json['keyLoc'] = input(f"your public and private key directory (default - '{param_json['keyLoc']}'): ") or param_json['keyLoc']

param_json['blockchainLoc'] = input(f"your .blockchain file directory (default - {param_json['blockchainLoc']}): ") or param_json['blockchainLoc']

with open(f"./config/{param_json['nodeID']}.json", "w") as f:
    f.write(json.dumps(param_json))
print("config initialization completed.")