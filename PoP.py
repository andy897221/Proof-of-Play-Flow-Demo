import popGame.main as _conn
import popBlockchain.main as _blockchain


class PoP:

    def __init__(self, nodeID):
        self.nodeID = nodeID
        return

    def run_conn(self):
        _conn.main(self.nodeID)

    def run_blckchain(self):
        _blockchain.main(self.nodeID)