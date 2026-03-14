import requests
import json

def test_northbound_eastmoney():
    # Try to find Northbound funds data
    # Common codes for Northbound/Southbound
    # BK0701: HK->SH (North) ?
    # BK0804: Northbound ?
    
    codes = ["90.BK0707", "90.BK0804", "1.000001", "0.399001"]
    
    for code in codes:
        url = f"http://push2.eastmoney.com/api/qt/stock/get?secid={code}&fields=f57,f58,f107,f43,f169,f170,f171,f47,f48,f60,f46,f44,f45,f168,f50,f162,f177,f62,f135,f136,f265"
        # f62 is usually net inflow?
        
        try:
            resp = requests.get(url, timeout=5)
            data = resp.json()
            if data['data']:
                print(f"Code: {code} - Found Data: {data['data']['f58']} (Name?)")
                print(data)
            else:
                print(f"Code: {code} - No Data")
        except Exception as e:
            print(f"Code: {code} - Error: {e}")

def test_northbound_flow_api():
    # EastMoney Northbound Flow API (History/Kline)
    # http://push2.eastmoney.com/api/qt/kline/get?lmt=0&klt=101&fields1=f1%2Cf2%2Cf3%2Cf7&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf62%2Cf63%2Cf64%2Cf65&secid=1.000001
    # Try to find the correct secid for Northbound
    
    # Try to search for "Northbound" in concept list
    url = "http://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=20&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f3&fs=m:13+t:2&fields=f12,f14"
    # fs=m:13+t:2 might be HK market or Connect
    
    try:
        resp = requests.get(url, timeout=5)
        print("Clist Response (HK/Connect?):", resp.text[:500])
    except:
        pass

if __name__ == "__main__":
    test_northbound_eastmoney()
    # test_northbound_flow_api()
