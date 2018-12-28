from py2p import mesh
import asyncio, argparse, time, sys

loop = asyncio.get_event_loop()

parser = argparse.ArgumentParser()
parser.add_argument("-b", "--bootstrap", type=int, help="whether this node in boostrap node")
parser.add_argument("-p", "--myPort", type=int, help="my port")
args = parser.parse_args()

myPort = args.myPort
sock = mesh.MeshSocket('0.0.0.0', myPort)
if args.bootstrap == 0:
    sock.connect('127.0.0.1', 1000)
    time.sleep(1)
    print(sock.routing_table)
bootstrapID = ""
sock.debug_level = 5

# async def readHandler():
async def readHandler():
    global bootstrapID
    while True:
        msg = sock.recv()
        if msg is not None:
            decodedMsg = msg.packets[1]
            if "hello" in str(decodedMsg):
                print("hi from {}".format(msg.sender))
            else:
                bootstrapID = decodedMsg
                print("bootstrap id is "+str(bootstrapID))
            if args.bootstrap == 1: msg.reply(sock.id)
            # msg.sender, msg.reply()
        await asyncio.sleep(1)
    return

count = 0
async def main():
    global sock, args, bootstrapID, count
    if args.bootstrap == 0:
        print("msg sent")
        sock.send("hello bootstrap")
    if myPort == 1002:
        while True:
            if count < 10:
                count += 1
                await asyncio.sleep(1)
                continue
            # connList = list(sock.routing_table.values())
            # for conn in connList: sock.disconnect(conn)
            print("disconnecting "+str(bootstrapID))
            sock.disconnect(sock.routing_table[bootstrapID])
            print("ending program...")
            sys.exit()
    return

try:
    future = [readHandler(), main()]
    loop.run_until_complete(asyncio.gather(*future))
except KeyboardInterrupt:
    pass
finally:
    print("ending program...")
    loop.close()