import urllib.request, json, os, uuid

BASE_URL = 'http://127.0.0.1:8001/api/v1'

def api_call(url, method='GET', data_dict=None, token=None):
    headers = {}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    if data_dict is not None:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(data_dict).encode()
    else:
        data = None

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        res = urllib.request.urlopen(req)
        return res.status, res.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()

# Get tokens for all 4 roles
roles = ['officer', 'admin', 'retailer', 'consumer']
tokens = {}
for r in roles:
    email = r + '@maars.gov.in' if r != 'retailer' else 'retailer@store.in'
    st, b = api_call(BASE_URL + '/auth/login', 'POST', {'email': email, 'password': 'Password123!'})
    tokens[r] = json.loads(b.decode())['access_token']

dummy_insp_id = str(uuid.uuid4())
endpoints = [
    ('POST /scans/upload', 'POST', BASE_URL + '/scans/upload', {'client_submission_id': str(uuid.uuid4()), 'area_id': str(uuid.uuid4())}),
    ('GET /rules/', 'GET', BASE_URL + '/rules/', None),
    ('POST /rules/', 'POST', BASE_URL + '/rules/', {'rule_code': 'TEST', 'category': 'test', 'statutory_reference': 'test', 'rule_type': 'presence', 'target_field': 'test', 'check_definition': {}}),
    ('GET /admin/analytics/overview', 'GET', BASE_URL + '/admin/analytics/overview', None),
    ('GET /admin/users', 'GET', BASE_URL + '/admin/users', None),
    ('GET /violations/{id}', 'GET', BASE_URL + '/violations/' + dummy_insp_id, None),
    ('POST /customer/scan', 'POST', BASE_URL + '/customer/scan', None), # Multi-part endpoint without body -> 422
]

print('ENDPOINT | ANONYMOUS | OFFICER | ADMIN | RETAILER | CONSUMER')
print('---|---|---|---|---|---')
for name, m, url, body in endpoints:
    st_anon, _ = api_call(url, m, body, None)
    st_off, _ = api_call(url, m, body, tokens['officer'])
    st_adm, _ = api_call(url, m, body, tokens['admin'])
    st_ret, _ = api_call(url, m, body, tokens['retailer'])
    st_con, _ = api_call(url, m, body, tokens['consumer'])
    print('%s | %d | %d | %d | %d | %d' % (name, st_anon, st_off, st_adm, st_ret, st_con))
