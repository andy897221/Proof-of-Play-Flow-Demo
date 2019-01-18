import os, sys

def call():
    return os.path.isfile("helloWorld.txt")

def call_abs(file):
    return os.path.abspath(file)

def call_real_abs():
    return os.path.abspath(__file__)

def call_sys_arg():
    return os.path.abspath(sys.argv[0])