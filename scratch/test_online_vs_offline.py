import urllib.request
import json
import sys

def test():
    # 1. Login user
    req = urllib.request.Request('http://localhost:8000/auth/login', data=json.dumps({'email': 'venu@company.com', 'password': 'password123'}).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        u_token = json.loads(resp.read().decode())['access_token']
        
    u_headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {u_token}'}

    # 2. Test Online activity diagnostic response (Application UI)
    req = urllib.request.Request('http://localhost:8000/chat/sessions', data=b'{}', headers=u_headers)
    with urllib.request.urlopen(req) as resp:
        session = json.loads(resp.read().decode())
        s_id1 = session['id']

    req = urllib.request.Request(f'http://localhost:8000/chat/sessions/{s_id1}/messages', data=json.dumps({
        'content': 'I want to perform Application UI changes and fix button layout'
    }).encode(), headers=u_headers)
    with urllib.request.urlopen(req) as resp:
        res1 = json.loads(resp.read().decode())
        content1 = res1.get('response', '')
        print("\n--- ONLINE ACTIVITY (Application UI) AI RESPONSE ---")
        print(content1.encode('ascii', 'ignore').decode('ascii'))
        # Check that it DOES NOT ask for maintenance window / downtime
        assert "Downtime / Maintenance Window" not in content1, "Online activity should not ask for maintenance window!"
        assert "Prerequisites Status" in content1

    # 3. Test Offline activity diagnostic response (Application Versioning)
    req = urllib.request.Request('http://localhost:8000/chat/sessions', data=b'{}', headers=u_headers)
    with urllib.request.urlopen(req) as resp:
        session = json.loads(resp.read().decode())
        s_id2 = session['id']

    req = urllib.request.Request(f'http://localhost:8000/chat/sessions/{s_id2}/messages', data=json.dumps({
        'content': 'I want to perform application version maintenance and upgrade binaries'
    }).encode(), headers=u_headers)
    with urllib.request.urlopen(req) as resp:
        res2 = json.loads(resp.read().decode())
        content2 = res2.get('response', '')
        print("\n--- OFFLINE ACTIVITY (Application Version) AI RESPONSE ---")
        print(content2.encode('ascii', 'ignore').decode('ascii'))
        # Check that it DOES ask for maintenance window / downtime
        assert "Downtime / Maintenance Window" in content2, "Offline activity must ask for maintenance window!"
        assert "Prerequisites Status" in content2

    print("\nALL ONLINE VS OFFLINE / HYBRID VERIFICATIONS PASSED!")

if __name__ == '__main__':
    test()