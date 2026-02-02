import requests
import uuid

XUI_BASE_URL = "https://127.0.0.1:31308"
XUI_USERNAME = "admin"
XUI_PASSWORD = "admin"

session = requests.Session()

def login():
    r = session.post(
        f"{XUI_BASE_URL}/login",
        json={"username": XUI_USERNAME, "password": XUI_PASSWORD},
        verify=False,
    )
    r.raise_for_status()

def create_vpn_client(user_id: int):
    email = f"user_{user_id}_{uuid.uuid4().hex[:6]}"

    payload = {
        "email": email,
        "enable": True,
        "limitIp": 1,
        "totalGB": 0,
        "expiryTime": 0,
    }

    r = session.post(
        f"{XUI_BASE_URL}/panel/api/inbounds/addClient",
        json=payload,
        verify=False,
    )
    r.raise_for_status()

    vless_url = f"vless://{email}@YOUR_DOMAIN:443?encryption=none#AsberryVPN"

    return {
        "email": email,
        "vless_url": vless_url,
    }

