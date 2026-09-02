import urllib.request
import json

def check():
    req = urllib.request.Request('http://localhost:8000/auth/login', data=json.dumps({'email': 'venu@company.com', 'password': 'password123'}).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        token = json.loads(resp.read().decode())['access_token']

    req = urllib.request.Request('http://localhost:8000/categories', headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req) as resp:
        cats = json.loads(resp.read().decode())
        print("ACTIVE CATEGORIES IN SYSTEM:")
        for c in cats:
            print(f"- {c['name']} ({c.get('description', '')})")

if __name__ == '__main__':
    check()

