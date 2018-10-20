import asyncio, time
from asyncio import Queue

async def helloWorld1(loop):
    while True:
        print("hello world 1")
        newFunc = loop.create_task(helloWorld2())
        await asyncio.sleep(1)

async def helloWorld2():
    while True:
        print("hello world 2")
        await asyncio.sleep(2)

loop = asyncio.get_event_loop()
try:
    asyncio.ensure_future(helloWorld1(loop))
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    print("closing loop")
    loop.close()

# NOPE IT DOESNT MAKE SENSE TO DO THIS