import requests

def test_zhcw():
    url = "http://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }
    
    for name in ["3d"]:
        params = {"name": name, "issueCount": 2}
        try:
            r = requests.get(url, params=params, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if "result" in data:
                    print(f"[{name}] Fetched {len(data['result'])} records")
                    print(data['result'])
        except Exception as e:
            print(f"[{name}] Exception: {e}")

test_zhcw()
