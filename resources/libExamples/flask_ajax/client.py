import requests, time

res = requests.post(f"http://127.0.0.1:3000/test", json={"hello": "world"})
print(res.json()["msg1"])