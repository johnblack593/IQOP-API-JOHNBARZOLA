import requests
import json

def test_raw_login():
    url = "https://auth.iqoption.com/api/v2/login"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    # Solo para ver si conecta
    try:
        print("Enviando POST raw a auth.iqoption.com...")
        resp = requests.post(url, json={}, headers=headers, timeout=15)
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text[:100]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_raw_login()
