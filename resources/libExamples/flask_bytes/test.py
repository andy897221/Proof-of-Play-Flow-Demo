from flask import Flask, send_file
import requests
from io import BytesIO
from threading import Thread
import time, pickle


def start_server():
    app = Flask(__name__)

    @app.route('/test', methods=['GET'])
    def test():
        msg = BytesIO()
        msg.write(pickle.dumps({"hello": "world"}))
        msg.seek(0)
        return send_file(msg, as_attachment=True, attachment_filename="msg")

    app.run(host='0.0.0.0', port=3000)

def ask():
    print(requests.get("http://127.0.0.1:3000/test").content)

if __name__ == '__main__':
    try:
        server = Thread(target=start_server)
        server.daemon = True
        server.start()
        time.sleep(2)
        ask()
        while True: time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        exit()