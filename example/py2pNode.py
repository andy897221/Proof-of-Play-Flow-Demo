from py2p import mesh
import time, argparse, asyncio

# script argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("-m", "--matchID", type=str, help="the match ID to join for this player (node)")
parser.add_argument("-p", "--port", type=int, help="the opening port number for p2p connection")
args = parser.parse_args()

# p2p network setup
sock = mesh.MeshSocket('0.0.0.0', args.port)
sock.connect('192.168.0.180', 5555)
# concurrency handler
loop = asyncio.get_event_loop()

def connEstabTrigger():
    return

async def readHandler():
    while True:
        msg = sock.recv()
        if msg is not None: print(msg.packets)
        await asyncio.sleep(1)
    return

def main():
    global sock
    print("MatchID: "+ args.matchID)
    sock.send("Hello from node")
    try:
        asyncio.ensure_future(readHandler())
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        print("ending program...")
        loop.close()
    return

time.sleep(1)
main()