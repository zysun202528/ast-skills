import requests

def test_breadth():
    url = "http://qt.gtimg.cn/q=sh000001,sz399001"
    resp = requests.get(url)
    print(resp.text)

if __name__ == "__main__":
    test_breadth()