import os
import time
import json
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

sent_frames = []
recv_frames = []

def handle_ws(ws):
    print(f"\n[WS CONNECTED] {ws.url}")
    
    def on_send(payload):
        text = payload if isinstance(payload, str) else payload.decode('utf-8', errors='ignore')
        print(f"\n---> [SEND] {text[:500]}")
        sent_frames.append(text)
        with open("examples/debug_s13_frames.json", "w", encoding="utf-8") as f:
            json.dump({"sent": sent_frames, "recv": recv_frames}, f, indent=2)
        
    def on_recv(payload):
        text = payload if isinstance(payload, str) else payload.decode('utf-8', errors='ignore')
        keywords = ["get-instruments", "initialization-data", "underlying", "position-changed", "subscribeMessage", "type\":\"instruments"]
        if any(kw in text for kw in keywords):
            print(f"\n<--- [RECV TARGET] {text[:500]}")
            recv_frames.append(text)
            with open("examples/debug_s13_frames.json", "w", encoding="utf-8") as f:
                json.dump({"sent": sent_frames, "recv": recv_frames}, f, indent=2)

    ws.on("framesent", on_send)
    ws.on("framereceived", on_recv)

def run():
    print("Iniciando Chromium en modo visible (headless=False)...")
    print("Por favor interactua con el navegador si te pide captcha.")
    print("Luego haz clic en el menu +, selecciona Forex, Digital o CFD.")
    print("La consola registrara el trafico de WebSockets en tiempo real.")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.on("websocket", handle_ws)
        
        page.goto("https://login.iqoption.com/en/login")
        
        print(f"Fill credentials para: {IQ_EMAIL}")
        try:
            page.fill('input[type="email"], input[name="email"], [placeholder*="Email"], [placeholder*="Phone"]', IQ_EMAIL, timeout=5000)
            page.fill('input[type="password"]', IQ_PASSWORD, timeout=5000)
            page.click('button[type="submit"], button:has-text("Log In")')
            print("Credenciales enviadas! Resuelve el Captcha si aparece...")
        except Exception as e:
            print(f"No se pudo autocompletar, por favor inicia sesion manualmente. ({e})")
        
        print("\n\n==== INTERCEPTOR ACTIVO ====")
        print("Tienes 90 segundos para hacer los clics requeridos manuales...")
        time.sleep(90)
        browser.close()
        
        print("Sesion terminada. Payloads guardados en examples/debug_s13_frames.json")

if __name__ == "__main__":
    run()
