from threading import Thread
import time

def testing():
    while True:
        print("testing")
        time.sleep(1000000)

if __name__ == '__main__':
    try:
        Thread(target=testing).start()
        while True:
            time.sleep(1)
            print("I am running too")
    except (KeyboardInterrupt, SystemExit):
        print("terminating...")