from flask import Flask, request
import requests
from threading import Thread
import time, pickle

def start_server():
    app = Flask(__name__)

    @app.route('/test', methods=['POST'])
    def test():
        print(pickle.loads(request.get_data()))
        return "", 200

    app.run(host='0.0.0.0', port=3000)

try:
    server = Thread(target=start_server)
    server.daemon = True
    server.start()
    requests.post('http://127.0.0.1:3000/test', data=pickle.dumps({b'123': b'456'}))
    while True: time.sleep(1)
except (KeyboardInterrupt, SystemExit):
    exit()