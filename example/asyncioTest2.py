import asyncio, time

async def helloWorld1():
    for i in range(0,5):
        print("hello world 1")
        await asyncio.sleep(1)

async def helloWorld2():
    for i in range(0,5):
        for j in range(0,5):
            print("hello world 2")
            await asyncio.sleep(2)
        await asyncio.sleep(2)

loop = asyncio.get_event_loop()
try:
    futures = [loop.create_task(helloWorld1()) , loop.create_task(helloWorld2())]
    loop.run_until_complete(asyncio.gather(*futures))
except KeyboardInterrupt:
    pass
finally:
    print("closing loop")
    loop.close()