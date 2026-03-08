import requests

def debug_factors():
    # Test Sina for Currency
    # Sina often uses 'fx_susdcny' or 'USDCNY'
    # Try: http://hq.sinajs.cn/list=fx_susdcny
    
    urls = [
        "http://hq.sinajs.cn/list=fx_susdcny",
        "http://hq.sinajs.cn/list=USDCNY",
        "http://qt.gtimg.cn/q=fl_000001", # Maybe?
        "http://web.ifzq.gtimg.cn/appstock/app/kline/kline?param=usdcny,day,,,1,qfq" # JSON endpoint
    ]
    
    for url in urls:
        print(f"Fetching: {url}")
        try:
            resp = requests.get(url, timeout=3)
            print(f"Response: {resp.text[:200]}") # Truncate
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    debug_factors()
