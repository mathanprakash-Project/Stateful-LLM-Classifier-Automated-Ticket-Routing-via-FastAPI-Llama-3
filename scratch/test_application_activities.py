import urllib.request
import json

def test():
    # 1. Login user
    req = urllib.request.Request('http://localhost:8000/auth/login', data=json.dumps({'email': 'venu@company.com', 'password': 'password123'}).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        u_token = json.loads(resp.read().decode())['access_token']
        
    u_headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {u_token}'}
    
    # 2. Get active categories
    req = urllib.request.Request('http://localhost:8000/categories', headers=u_headers)
    with urllib.request.urlopen(req) as resp:
        cats = json.loads(resp.read().decode())
    
    cat_names = [c['name'] for c in cats]
    print(f"Categories verified: {cat_names}")
    assert len(cats) == 4
    assert "Security" not in cat_names
    assert "Network" not in cat_names
    assert "Server / Infrastructure" not in cat_names
    assert "Database" not in cat_names
    
    # 3. Test chat session triage draft generation for Version Upgrade
    req = urllib.request.Request('http://localhost:8000/chat/sessions', data=b'{}', headers=u_headers)
    with urllib.request.urlopen(req) as resp:
        session = json.loads(resp.read().decode())
        s_id = session['id']
        
    req = urllib.request.Request(f'http://localhost:8000/chat/sessions/{s_id}/messages', data=json.dumps({
        'content': 'I need to perform application version maintenance and upgrade to release 6.4.1 tonight'
    }).encode(), headers=u_headers)
    with urllib.request.urlopen(req) as resp:
        chat_res = json.loads(resp.read().decode())
        draft = chat_res.get('draft')
        if draft:
            d_data = draft.get('draft_data', {})
            print(f"Generated Draft Title: \"{d_data.get('title')}\"")
            print(f"Generated Draft Category: \"{d_data.get('category_name')}\"")
            print(f"Generated Draft Execution Mode: \"{d_data.get('execution_mode')}\"")
            print(f"Generated Draft Priority: \"{d_data.get('priority')}\"")
            assert d_data.get('title') == 'Application Version Maintenance'
            assert d_data.get('priority') == 'critical'
            assert d_data.get('execution_mode') == 'Offline'

    print("\nALL APPLICATION ACTIVITY & STATIC TITLE RULES VERIFIED!")

if __name__ == '__main__':
    test()

