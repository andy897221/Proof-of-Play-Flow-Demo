from flask import Flask, request
import time, json

app = Flask(__name__)

@app.route("/test", methods=['POST'])
def testing():
    print(f"msg received {request.data}")
    time.sleep(5)
    return json.dumps({"msg1": "hello", "msg2": "world"}), 200

app.run(host='0.0.0.0', port=3000)