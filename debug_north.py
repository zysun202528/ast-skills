import requests

def test_northbound():
    url_north = "http://qt.gtimg.cn/q=ff_north_cney"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'http://gu.qq.com/'
    }
    
    try:
        print(f"Fetching: {url_north}")
        resp = requests.get(url_north, headers=headers, timeout=5)
        print(f"Status Code: {resp.status_code}")
        print(f"Raw Response: {resp.text}")
        
        parts = resp.text.split(';')
        for part in parts:
            if "ff_north_cney" in part:
                vals = part.split('~')
                print(f"Parsed Values: {vals}")
                if len(vals) > 3:
                    print(f"Northbound Net Inflow: {vals[3]}")
                else:
                    print("Could not parse Northbound Net Inflow")
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_northbound()
