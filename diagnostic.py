import json
d = json.load(open('notebooks/outputs/dashboard/dashboard_data.json'))
print([k for k in d['disputes'][0].keys() if 'customer' in k.lower() or 'city' in k.lower()])