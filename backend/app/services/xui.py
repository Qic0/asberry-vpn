import requests
import uuid

class XUIService:
    def __init__(self, base_url, panel_path, username, password):
        self.base_url = base_url
        self.panel_path = panel_path
        self.session = requests.Session()

        self.session.post(
            f"{self.base_url}/{self.panel_path}/login",
            json={"username": username, "password": password}
        )

    def add_client(self, inbound_id: int, telegram_id: int):
        client_uuid = str(uuid.uuid4())
        email = f"tg_{telegram_id}"

        payload = {
            "id": inbound_id,
            "settings": {
                "clients": [{
                    "id": client_uuid,
                    "email": email,
                    "enable": True
                }]
            }
        }

        r = self.session.post(
            f"{self.base_url}/{self.panel_path}/panel/api/inbounds/addClient",
            json=payload
        )
        r.raise_for_status()

        return client_uuid

