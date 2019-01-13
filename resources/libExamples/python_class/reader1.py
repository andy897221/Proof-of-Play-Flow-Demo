import time
from concurrent.futures import ThreadPoolExecutor
import read2
import data_class

executor = ThreadPoolExecutor(1)

executor.submit(read2.test)
print(data_class.data.a)
data_class.data.a = "reader 1 received!"
time.sleep(3)
print(data_class.data.a)