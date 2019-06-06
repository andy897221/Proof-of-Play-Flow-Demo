import socket
import sys
import _thread as thread
import time

def server(*settings):
    try:
        dock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dock_socket.bind(('', settings[0]))
        dock_socket.listen(5)
        while True:
            client_socket = dock_socket.accept()[0]
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect((settings[1], settings[2]))
            thread.start_new_thread(forward, (client_socket, server_socket))
            thread.start_new_thread(forward, (server_socket, client_socket))
    finally:
        thread.start_new_thread(server, settings)

def forward(source, destination):
    string = ' '
    while string:
        string = source.recv(32768)
        if string:
            destination.sendall(string)
        else:
            source.shutdown(socket.SHUT_RD)
            destination.shutdown(socket.SHUT_WR)

class Mapping:
    def __init__(self, src_port, dst_port):
        self.src_port = src_port
        self.dst_port = dst_port
        self.setting = (self.src_port, "127.0.0.1", self.dst_port)
        print("[+]Running mapping " + str(self.src_port) + " >>>>>> " + "127.0.0.1 " + str(self.dst_port))

    def run(self):
        thread.start_new_thread(server, self.setting)
        while True:
            time.sleep(60)
