import requests

url_token = "http://localhost:8000/api/v1/auth/token"
data = {"username": "admin", "password": "admin"}

res_token = requests.post(url_token, data=data)
token = res_token.json()["access_token"]

url_me = "http://localhost:8000/api/v1/auth/me"
headers = {"Authorization": f"Bearer {token}"}
res_me = requests.get(url_me, headers=headers)

print(f"Me Status: {res_me.status_code}")
print(f"Me Response: {res_me.json()}")
