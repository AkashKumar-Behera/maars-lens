import os, time, json, urllib.request, io

BASE_URL = 'http://127.0.0.1:8001/api/v1'

# Login as consumer/customer
req = urllib.request.Request(
    BASE_URL + '/auth/login',
    data=json.dumps({'email': 'consumer@maars.gov.in', 'password': 'Password123!'}).encode(),
    headers={'Content-Type': 'application/json'}
)
token = json.loads(urllib.request.urlopen(req).read().decode())['access_token']

def test_scan_api(image_path):
    with open(image_path, 'rb') as f:
        img_bytes = f.read()

    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    headers = {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'multipart/form-data; boundary=' + boundary
    }
    body = io.BytesIO()
    body.write(('--' + boundary + '\r\n').encode())
    body.write(('Content-Disposition: form-data; name=\"file\"; filename=\"' + os.path.basename(image_path) + '\"\r\n').encode())
    body.write(('Content-Type: image/png\r\n\r\n').encode())
    body.write(img_bytes)
    body.write(b'\r\n')
    body.write(('--' + boundary + '\r\n').encode())
    body.write(('Content-Disposition: form-data; name=\"panel_type\"\r\n\r\n').encode())
    body.write(b'front\r\n')
    body.write(('--' + boundary + '--\r\n').encode())

    req = urllib.request.Request(BASE_URL + '/customer/scan', data=body.getvalue(), headers=headers, method='POST')
    t0 = time.time()
    try:
        res = urllib.request.urlopen(req)
        latency = time.time() - t0
        return res.status, json.loads(res.read().decode()), latency
    except urllib.error.HTTPError as e:
        latency = time.time() - t0
        return e.code, json.loads(e.read().decode()), latency

fixtures = [
    # 8 Existing
    'backend/tests/fixtures/labels/01_compliant_bilingual.png',
    'backend/tests/fixtures/labels/02_missing_mrp.png',
    'backend/tests/fixtures/labels/03_tiny_font.png',
    'backend/tests/fixtures/labels/04_missing_address.png',
    'backend/tests/fixtures/labels/05_imported_no_origin.png',
    'backend/tests/fixtures/labels/06_blurry_label.png',
    'backend/tests/fixtures/labels/07_hindi_english_mix.png',
    'backend/tests/fixtures/labels/08_multi_panel.png',
    # 5 Newly Generated
    'audit_output/generated_labels/09_rotated_15deg.png',
    'audit_output/generated_labels/10_glare_reflection.png',
    'audit_output/generated_labels/11_low_light.png',
    'audit_output/generated_labels/12_non_permitted_units.png',
    'audit_output/generated_labels/13_multi_mrp.png',
]

print('FILE | STATUS | VERDICT | FACTS EXTRACTED | VIOLATIONS | LATENCY (s)')
print('---|---|---|---|---|---')

results_summary = []
for p in fixtures:
    fname = os.path.basename(p)
    st, data, lat = test_scan_api(p)
    if st == 200:
        verdict = data.get('compliance_status') or data.get('status')
        facts = data.get('extracted_facts') or {}
        violations = data.get('violations') or []
        facts_str = ', '.join(facts.keys()) if facts else 'None'
        print('%s | %d | %s | %d fields | %d violations | %.2fs' % (fname, st, verdict, len(facts), len(violations), lat))
        results_summary.append({
            'file': fname,
            'status': st,
            'verdict': verdict,
            'facts_count': len(facts),
            'facts': list(facts.keys()),
            'violations_count': len(violations),
            'violations': [v.get('rule_code') for v in violations],
            'latency': round(lat, 3)
        })
    else:
        detail = data.get('detail', 'Error')
        print('%s | %d | ERROR: %s | 0 fields | 0 violations | %.2fs' % (fname, st, str(detail)[:30], lat))
        results_summary.append({
            'file': fname,
            'status': st,
            'verdict': 'error',
            'detail': detail,
            'latency': round(lat, 3)
        })

with open('audit_output/label_benchmark_results.json', 'w') as f:
    json.dump(results_summary, f, indent=2)
