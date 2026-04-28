import os
import sys

# Path setup
sys.path.append("d:/Programacion/API-IQ/IQOP-API-JOHNBARZOLA")

def load_env():
    env_path = 'd:/Programacion/API-IQ/IQOP-API-JOHNBARZOLA/.env'
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")

def main():
    load_env()
    from iqoptionapi.stable_api import IQ_Option
    email = os.environ.get('IQ_EMAIL')
    password = os.environ.get('IQ_PASSWORD')
    
    iq = IQ_Option(email, password)
    print(f"Probando login para: {email}")
    check, reason = iq.connect()
    print(f"Resultado: {check}, Reason: {reason}")

if __name__ == "__main__":
    main()
