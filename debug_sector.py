import requests

def test_eastmoney_sector():
    # Test getting data for a sector (e.g., Power/Electricity)
    # 561560: Power Construction ETF
    url = "http://qt.gtimg.cn/q=sh561560,sz159611"
    
    try:
        resp = requests.get(url)
        print(f"Sector URL: {url}")
        print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

def test_northbound_eastmoney():
    # Try to find Northbound funds data
    # Often it's under a special code.
    # Let's try to get the list of concepts to see if we can find Northbound.
    pass

if __name__ == "__main__":
    test_eastmoney_sector()
