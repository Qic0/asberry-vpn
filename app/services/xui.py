import requests

class XUIClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.login(username, password)

    def login(self, username: str, password: str):
        resp = self.session.post(
            f"{self.base_url}/login",
            data={"username": username, "password": password},
            verify=False,
        )
        resp.raise_for_status()

    def add_client(self, inbound_id: int, email: str):
        payload = {
            "id": inbound_id,
            "settings": {
                "clients": [
                    {
                        "email": email,
                        "enable": True
                    }
                ]
            }
        }
        resp = self.session.post(
            f"{self.base_url}/panel/api/inbounds/addClient",
            json=payload,
            verify=False,
        )
        resp.raise_for_status()
        data = resp.json()
        return data

    def get_subscription(self, email: str):
        return f"{self.base_url}/sub/{email}"

