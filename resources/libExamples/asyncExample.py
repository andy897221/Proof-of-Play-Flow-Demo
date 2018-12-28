import asyncio

loop = asyncio.get_event_loop()

async def func1():
    while True:
        print("hello 1")
        await asyncio.sleep(1)
    return

async def func2():
    print("hello 2")
    return

try:
    future = [func1(), func2()]
    loop.run_until_complete(asyncio.gather(*future))
except KeyboardInterrupt:
    pass
finally:
    print("ending program...")
    loop.close()