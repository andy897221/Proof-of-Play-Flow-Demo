from threading import Thread
import time, sys

class val:
    val = 0

def printing(testing):
    while True:
        print(testing)
        time.sleep(1)

def myDec(testing):
    def wtf(func):
        def func_wrapper():
            try:
                print1 = Thread(target=printing, args=(testing,))
                print2 = Thread(target=printing, args=(testing,))
                print1.daemon = True
                print2.daemon = True
                print1.start()
                print2.start()
                func()
                while print1.isAlive() or print2.isAlive(): pass
            except (KeyboardInterrupt, SystemExit):
                print("main thread terminating...")
                sys.exit()
        return func_wrapper
    return wtf

@myDec(1)
def test():
    print("two thread has ran! and I executed my code!")
    return

test()