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