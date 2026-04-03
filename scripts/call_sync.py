import urllib.request, json, http.cookiejar
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Login as admin/admin
login_data = json.dumps({'username':'admin','password':'admin'}).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:5000/api/login', data=login_data, headers={'Content-Type':'application/json'})
resp = opener.open(req)
print('LOGIN STATUS', resp.getcode())
print(resp.read().decode('utf-8'))

# Call read-only sync-data
req2 = urllib.request.Request('http://127.0.0.1:5000/api/sync-data')
resp2 = opener.open(req2)
print('SYNC-DATA STATUS', resp2.getcode())
print(resp2.read().decode('utf-8'))
