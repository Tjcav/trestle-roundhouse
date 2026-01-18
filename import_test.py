import requests
url = 'http://localhost:9200/claims/import'
file_path = '/workspaces/trestle-roundhouse/apps/control-point/frontend/spec_001_ai_governed_system_development_methodology.md'
with open(file_path, 'rb') as f:
    files = {'file': (file_path, f, 'text/markdown')}
    response = requests.post(url, files=files)
    print('Status:', response.status_code)
    print('Response:', response.text)
