import requests

def debug_stock_data(symbol):
    # Test Sector ETFs
    # 512880: Securities (Broker)
    # 512690: Liquor (Alcohol) - Wait, is there a Liquor ETF? 
    # Let's try:
    # sh512880 (Securities)
    # sh512480 (Semi)
    # sh516160 (New Energy)
    # sh512010 (Pharma)
    # sh510150 (Consumer)
    # sh512800 (Bank)
    
    etfs = [
        "sh512880", # Securities
        "sh512480", # Semi
        "sh516160", # New Energy
        "sh512010", # Pharma
        "sh510150", # Consumer
        "sh512800"  # Bank
    ]
    
    url = f"http://qt.gtimg.cn/q={','.join(etfs)}"
    
    print(f"Fetching ETFs: {url}...")
    try:
        resp = requests.get(url, timeout=5)
        print("Response text (raw):")
        print(resp.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_stock_data("600519")
