import json, uuid, urllib.request, urllib.error
from pathlib import Path
from PIL import Image

base = 'http://localhost:8000'
img_path = Path('tmp_segment_test.png')
Image.new('RGB', (64, 64), (255, 0, 0)).save(img_path)

checks = []

with urllib.request.urlopen(base + '/health') as r:
    body = r.read().decode()
    checks.append(('health', r.status, body))

with urllib.request.urlopen(base + '/analytics') as r:
    body = r.read().decode()
    checks.append(('analytics', r.status, body))

payload = json.dumps({
    'femurWidth': 65.5,
    'femurAP': 58.4,
    'tibiaWidth': 71.8,
    'tibiaAP': 47.2,
}).encode()
req = urllib.request.Request(base + '/implant-match', data=payload, headers={'Content-Type': 'application/json'}, method='POST')
with urllib.request.urlopen(req) as r:
    body = r.read().decode()
    checks.append(('implant', r.status, body))

boundary = '----PythonBoundary' + uuid.uuid4().hex
body_bytes = (
    f'--{boundary}\r\n'
    'Content-Disposition: form-data; name="file"; filename="tmp_segment_test.png"\r\n'
    'Content-Type: image/png\r\n\r\n'
).encode() + img_path.read_bytes() + f'\r\n--{boundary}--\r\n'.encode()
seg_req = urllib.request.Request(
    base + '/api/v1/segment',
    data=body_bytes,
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'},
    method='POST',
)
with urllib.request.urlopen(seg_req) as r:
    body = r.read().decode()
    checks.append(('segment', r.status, body))

for name, status, body in checks:
    print(f'[{name}] status={status}')
    print(body[:800])
    print('---')
