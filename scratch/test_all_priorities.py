import urllib.request
import json

def test():
    req = urllib.request.Request('http://localhost:3000/api/auth/login', data=json.dumps({'email': 'venu@company.com', 'password': 'password123'}).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        u_token = json.loads(resp.read().decode())['access_token']
        
    u_headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {u_token}'}

    activities_tests = [
        ("I have an Application UI button issue and layout glitch", "Application UI Maintenance", "Online", "medium"),
        ("I have a File Management background log issue", "File Management Operations", "Online", "medium"),
        ("I need a Client Data Transfer from client 100 to client 200", "Client Data Transfer", "Hybrid", "high"),
        ("I need an Application Version upgrade to v6.0", "Application Version Maintenance", "Offline", "critical"),
    ]

    for user_prompt, exp_title, exp_mode, exp_prio in activities_tests:
        req = urllib.request.Request('http://localhost:3000/api/chat/sessions', data=b'{}', headers=u_headers)
        with urllib.request.urlopen(req) as resp:
            s_id = json.loads(resp.read().decode())['id']

        # Complete triage
        req = urllib.request.Request(f'http://localhost:3000/api/chat/sessions/{s_id}/messages', data=json.dumps({'content': user_prompt}).encode(), headers=u_headers)
        with urllib.request.urlopen(req) as resp:
            res1 = json.loads(resp.read().decode())
            draft1 = res1.get('draft')
        
        if not draft1:
            req = urllib.request.Request(f'http://localhost:3000/api/chat/sessions/{s_id}/messages', data=json.dumps({'content': 'Yes all prerequisites are completed and verified Saturday 11pm'}).encode(), headers=u_headers)
            with urllib.request.urlopen(req) as resp:
                res2 = json.loads(resp.read().decode())
                draft1 = res2.get('draft')

        assert draft1 is not None, f"Draft was not generated for {user_prompt}"
        d_data = draft1.get('draft_data', {})
        print(f"[{exp_title}] -> Mode: {d_data.get('execution_mode')} | Priority: {d_data.get('priority')}")
        assert d_data.get('execution_mode') == exp_mode, f"Expected mode {exp_mode}, got {d_data.get('execution_mode')}"
        assert d_data.get('priority') == exp_prio, f"Expected priority {exp_prio}, got {d_data.get('priority')}"

    print("\nALL 4 APPLICATION ACTIVITIES & MODE-PRIORITY MAPPINGS PERFECTLY VERIFIED!")

if __name__ == '__main__':
    test()

