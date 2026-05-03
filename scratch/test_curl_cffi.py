from curl_cffi import requests

def test_impersonate():
    url = "https://iqoption.com/api/appinit"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
    }
    try:
        s = requests.Session(impersonate="chrome110")
        resp = s.get(url, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Server: {resp.headers.get('Server')}")
        print(f"Body snippet: {resp.text[:100]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_impersonate()
