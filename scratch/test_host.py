import urllib.request
import json

def run():
    # 1. Login user
    req = urllib.request.Request('http://localhost:8000/auth/login', data=json.dumps({'email': 'venu@company.com', 'password': 'password123'}).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        u_token = json.loads(resp.read().decode())['access_token']
        
    u_headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {u_token}'}
    
    # 2. Get category and create ticket
    req = urllib.request.Request('http://localhost:8000/categories', headers=u_headers)
    with urllib.request.urlopen(req) as resp:
        cats = json.loads(resp.read().decode())
        
    req = urllib.request.Request('http://localhost:8000/tickets', data=json.dumps({
        'title': 'Test Customer Reopened Reason Flow',
        'description': 'Customer testing reopen reason and elevated high priority alert',
        'category_id': cats[0]['id'],
        'priority': 'medium'
    }).encode(), headers=u_headers)
    with urllib.request.urlopen(req) as resp:
        ticket = json.loads(resp.read().decode())
        t_id = ticket['id']
        t_num = ticket['ticket_number']
        t_pri = ticket['priority']
        print(f"Created ticket #{t_num} with initial priority: {t_pri}")
        
    # 3. Employee starts & resolves
    req = urllib.request.Request('http://localhost:8000/auth/login', data=json.dumps({'email': 'eegan@company.com', 'password': 'password123'}).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        e_token = json.loads(resp.read().decode())['access_token']
    e_headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {e_token}'}
    
    req = urllib.request.Request(f'http://localhost:8000/tickets/{t_id}/start-work', data=b'{}', headers=e_headers)
    with urllib.request.urlopen(req): pass
    req = urllib.request.Request(f'http://localhost:8000/tickets/{t_id}/complete-work', data=json.dumps({'notes': 'First resolve attempt complete'}).encode(), headers=e_headers)
    with urllib.request.urlopen(req): pass
    print("Employee marked ticket as Resolved.")
    
    # 4. User reopens with detailed reason
    detailed_reason = 'Database indexing failed on client_data table during version update.'
    req = urllib.request.Request(f'http://localhost:8000/tickets/{t_id}/reopen', data=json.dumps({'reason': detailed_reason}).encode(), headers=u_headers)
    with urllib.request.urlopen(req) as resp:
        reopened = json.loads(resp.read().decode())
        r_stat = reopened['status']
        r_pri = reopened['priority']
        r_cnt = reopened.get('meta_info', {}).get('reopen_count')
        r_rsn = reopened.get('meta_info', {}).get('latest_reopen_reason')
        print(f"Reopened Status: {r_stat}")
        print(f"Reopened Priority: {r_pri} (Elevated from medium)")
        print(f"Reopen Count: {r_cnt}/3")
        print(f"Recorded Reason: \"{r_rsn}\"")
        assert r_stat == 'reopened'
        assert r_pri == 'high'
        assert r_rsn == detailed_reason
        print("SUCCESS: Verified detailed reason recording and elevated HIGH priority on reopen!")

if __name__ == '__main__':
    run()

