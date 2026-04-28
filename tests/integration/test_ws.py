import websocket
import ssl
import certifi
import time

url = "wss://ws.iqoption.com/echo/websocket"
print(f"Connecting to {url}...")

def on_message(ws, message):
    print(f"Message: {message}")

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"Closed: {close_status_code} - {close_msg}")

def on_open(ws):
    print("Opened!")
    ws.close()

ws = websocket.WebSocketApp(url,
                          on_message=on_message,
                          on_error=on_error,
                          on_close=on_close)
ws.on_open = on_open

ws.run_forever(sslopt={"check_hostname": True, "cert_reqs": ssl.CERT_REQUIRED, "ca_certs": certifi.where()})
