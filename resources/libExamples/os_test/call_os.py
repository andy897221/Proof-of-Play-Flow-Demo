import run.run_os as run_os
import os

print(os.path.isfile("helloWorld.txt"))
print(run_os.call())

print(os.path.abspath(__file__))
print(run_os.call_abs(__file__))
print(run_os.call_real_abs())

print(run_os.call_sys_arg())