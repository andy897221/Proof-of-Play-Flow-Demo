from time import sleep
import multiprocessing as mp

count = mp.Value('i', 0)

def counter(count):
    print("Starting counter func")
    while True:
        count.value += 1
        sleep(2)
        print("Waking up for the {} time".format(count.value))

def printCounter(count):
    print("Printing function")
    while True:
        print("Counter value at {}".format(count.value))
        sleep(0.55)

def main():
    p1 = mp.Process(target = counter, args=(count,))
    p2 = mp.Process(target = printCounter, args =(count,))
    p1.start()
    p2.start()

if __name__ == "__main__":
    main()