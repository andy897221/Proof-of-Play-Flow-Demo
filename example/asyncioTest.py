import asyncio, time

async def helloWorld1():
    while True:
        print("hello world 1")
        await asyncio.sleep(1)

async def helloWorld2():
    while True:
        print("hello world 2")
        await asyncio.sleep(2)

loop = asyncio.get_event_loop()
try:
    asyncio.ensure_future(helloWorld1())
    asyncio.ensure_future(helloWorld2())
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    print("closing loop")
    loop.close()