import urllib.request, json, io, os, uuid

BASE_URL = 'http://127.0.0.1:8001/api/v1'

def api_call(url, method='GET', data_dict=None, token=None, files=None):
    headers = {}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    
    if files:
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        headers['Content-Type'] = 'multipart/form-data; boundary=' + boundary
        body = io.BytesIO()
        for k, (fname, fbytes, mtype) in files.items():
            body.write(('--' + boundary + '\r\n').encode())
            body.write(('Content-Disposition: form-data; name=\"' + k + '\"; filename=\"' + fname + '\"\r\n').encode())
            body.write(('Content-Type: ' + mtype + '\r\n\r\n').encode())
            body.write(fbytes)
            body.write(b'\r\n')
        if data_dict:
            for k, v in data_dict.items():
                body.write(('--' + boundary + '\r\n').encode())
                body.write(('Content-Disposition: form-data; name=\"' + k + '\"\r\n\r\n').encode())
                body.write(str(v).encode())
                body.write(b'\r\n')
        body.write(('--' + boundary + '--\r\n').encode())
        data = body.getvalue()
    elif data_dict is not None:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(data_dict).encode()
    else:
        data = None

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        res = urllib.request.urlopen(req)
        body = res.read()
        return res.status, body, dict(res.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)

# 1. Login as officer
st, b, h = api_call(BASE_URL + '/auth/login', method='POST', data_dict={'email': 'officer@maars.gov.in', 'password': 'Password123!'})
token = json.loads(b.decode())['access_token']
print('1. Officer Login: status=%d, token_len=%d' % (st, len(token)))

# 2. Upload / Create Scan via POST /scans/upload
sub_id = str(uuid.uuid4())
area_id = str(uuid.uuid4())
st, b, h = api_call(BASE_URL + '/scans/upload', method='POST', data_dict={
    'client_submission_id': sub_id,
    'area_id': area_id,
    'product_name': 'Audit Verification Biscuit',
    'brand_name': 'AuditCo'
}, token=token)
scan_resp = json.loads(b.decode())
scan_id = scan_resp['inspection_id']
print('2. Create Scan (/scans/upload): status=%d, scan_id=%s' % (st, scan_id))

# 3. Upload Image via POST /scans/{id}/images
img_path = 'backend/tests/fixtures/labels/01_compliant_bilingual.png'
with open(img_path, 'rb') as f:
    img_bytes = f.read()
st, b, h = api_call(
    BASE_URL + '/scans/' + scan_id + '/images',
    method='POST',
    data_dict={'panel_type': 'front'},
    token=token,
    files={'files': ('01_compliant_bilingual.png', img_bytes, 'image/png')}
)
img_upload_resp = json.loads(b.decode())
facts = img_upload_resp.get('extracted_facts', {})
print('3. Upload Image (/scans/%s/images): status=%d, facts_count=%d' % (scan_id, st, len(facts)))

# 4. Get Result via GET /scans/{id}/result
st, b, h = api_call(BASE_URL + '/scans/' + scan_id + '/result', method='GET', token=token)
results = json.loads(b.decode())
audit_items = results.get('audit_results', [])
print('4. Get Result (/scans/%s/result): status=%d, total_audit_results=%d' % (scan_id, st, len(audit_items)))

# 5. Manual Override via POST /scans/{id}/result
st, b, h = api_call(BASE_URL + '/scans/' + scan_id + '/result', method='POST', data_dict={
    'rule_code': 'LMPC-R6-NAME-ADDRESS',
    'manual_review_result': 'pass',
    'manual_review_reason': 'Officer physically checked manufacturer registration'
}, token=token)
print('5. Manual Override: status=%d' % st)

# 6. Finalize via POST /scans/{id}/finalize
st, b, h = api_call(BASE_URL + '/scans/' + scan_id + '/finalize', method='POST', data_dict={'officer_notes': 'Field verification complete'}, token=token)
fin_resp = json.loads(b.decode())
r_hash = fin_resp.get('report_hash', '')[:25]
is_fin = fin_resp.get('is_finalized')
print('6. Finalize: status=%d, is_finalized=%s, report_hash=%s...' % (st, is_fin, r_hash))

# 7. Exports
st_pdf, b_pdf, _ = api_call(BASE_URL + '/reports/' + scan_id + '/pdf', method='GET', token=token)
st_docx, b_docx, _ = api_call(BASE_URL + '/reports/' + scan_id + '/docx', method='GET', token=token)
st_xlsx, b_xlsx, _ = api_call(BASE_URL + '/reports/' + scan_id + '/xlsx', method='GET', token=token)
print('7. Exports:')
print('   PDF:  status=%d, size=%d bytes' % (st_pdf, len(b_pdf)))
print('   DOCX: status=%d, size=%d bytes' % (st_docx, len(b_docx)))
print('   XLSX: status=%d, size=%d bytes' % (st_xlsx, len(b_xlsx)))

# Save them into audit_output for inspection
os.makedirs('audit_output/verified_exports', exist_ok=True)
with open('audit_output/verified_exports/verified_report.pdf', 'wb') as f:
    f.write(b_pdf)
with open('audit_output/verified_exports/verified_report.docx', 'wb') as f:
    f.write(b_docx)
with open('audit_output/verified_exports/verified_report.xlsx', 'wb') as f:
    f.write(b_xlsx)
print('Export files saved to audit_output/verified_exports/')
