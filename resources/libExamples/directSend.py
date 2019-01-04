def directSend(playerID, msg):
    if playerID not in myConf.sock.routing_table: return playerID
    receiverNode = myConf.sock.routing_table[playerID]
    receiverNode.send(flags.whisper, flags.whisper, msg)
    return

async def _testDirectSend():
    global nodeMatchConfig 
    while True:
        print(nodeMatchConfig.myMatchPlayerIDs)
        if len(nodeMatchConfig.myMatchPlayerIDs) > 0: 
            notValidList = []
            for playerID in nodeMatchConfig.myMatchPlayerIDs:
                notValid = directSend(playerID, json.dumps({"msg": "hello, whispering from "+str(nodeConfig.myPort)}))
                if notValid is not None: notValidList += [notValid]
            notValidList = np.unique(notValidList)
            for playerID in notValidList: nodeMatchConfig.myMatchPlayerIDs.remove(playerID)
        await asyncio.sleep(1)
    return