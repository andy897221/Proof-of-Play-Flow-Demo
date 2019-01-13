import time
import data_class

def test():
    time.sleep(2)
    print(data_class.data.a)
    data_class.data.a = "my turn! I am reader 2!"
    time.sleep(10000)