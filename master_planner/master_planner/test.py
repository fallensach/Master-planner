import requests
url = "http://localhost:8000/api/get_courses/DAIM/7"
import json
data = json.dumps({"scheduler_id": 100})
# url = "http://127.0.0.1:8000/api/account/choice"
r = requests.get(url)

print(r.json())
