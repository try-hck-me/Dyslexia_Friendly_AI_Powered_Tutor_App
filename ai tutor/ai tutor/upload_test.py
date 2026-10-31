import requests

url = 'http://localhost:8000/upload'
filepath = r'sample_data\biology_cells.pdf'

with open(filepath, 'rb') as f:
    files = {'file': ('biology_cells.pdf', f, 'application/pdf')}
    res = requests.post(url, files=files)
    print(res.status_code)
    print(res.json())
