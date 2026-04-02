import requests
from bs4 import BeautifulSoup

def test_fetch(name):
    url_php = f"https://datachart.500.com/{name}/history/inc/history.php?limit=100000&start=00001&end=99999"
    r = requests.get(url_php, verify=False, timeout=15)
    r.encoding = "gb2312"
    soup = BeautifulSoup(r.text, "lxml")
    
    tdata = soup.find("tbody", attrs={"id": "tdata"})
    if tdata:
        trs = tdata.find_all("tr")
        if trs:
            tds = trs[0].find_all("td")
            print(f"[{name}] Data columns ({len(tds)}):")
            for i, td in enumerate(tds):
                print(f"  {i}: {td.get_text().strip()}")
    else:
        print(f"[{name}] Failed to find tdata in inc/history.php")
        
test_fetch("qlc")
test_fetch("sd")
