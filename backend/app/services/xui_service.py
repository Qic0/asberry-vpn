import httpx
import uuid
import json
from app.config import (
    XUI_BASE_URL,
    XUI_PANEL_PATH,
    XUI_USERNAME,
    XUI_PASSWORD,
    XUI_INBOUND_ID,
)

class XUIService:
    def __init__(self):
        self.client = httpx.Client(
            base_url=XUI_BASE_URL,
            timeout=15,
            verify=False,   # если есть self-signed cert
        )
        self._login()

    def _login(self):
        resp = self.client.post(
            f"/{XUI_PANEL_PATH}/login",
            json={
                "username": XUI_USERNAME,
                "password": XUI_PASSWORD,
            },
        )
        resp.raise_for_status()

    def get_inbound(self):
        resp = self.client.get(
            f"/{XUI_PANEL_PATH}/panel/api/inbounds/list"
        )
        resp.raise_for_status()
        data = resp.json()

        for inbound in data["obj"]:
            if inbound["id"] == XUI_INBOUND_ID:
                return inbound

        raise RuntimeError("Inbound not found")

    def add_client(self, telegram_id: int, device_number: int):
        inbound = self.get_inbound()

        settings = json.loads(inbound["settings"])

        client_uuid = str(uuid.uuid4())
        email = f"tg_{telegram_id}_{device_number}"

        new_client = {
            "id": client_uuid,
            "email": email,
            "enable": True,
            "limitIp": 0,
            "totalGB": 0,
            "expiryTime": 0,
            "tgId": telegram_id,
            "subId": "",
            "comment": "",
            "reset": 0,
        }

        settings["clients"].append(new_client)

        payload = {
            "id": inbound["id"],
            "settings": json.dumps(settings),
        }

        resp = self.client.post(
            f"/{XUI_PANEL_PATH}/panel/api/inbounds/update",
            json=payload,
        )
        resp.raise_for_status()

        return client_uuid

    def set_client_enabled(self, client_uuid: str, enabled: bool):
        inbound = self.get_inbound()
        settings = json.loads(inbound["settings"])

        for c in settings["clients"]:
            if c["id"] == client_uuid:
                c["enable"] = enabled
                break
        else:
            raise RuntimeError("Client not found")

        resp = self.client.post(
            f"/{XUI_PANEL_PATH}/panel/api/inbounds/update",
            json={
                "id": inbound["id"],
                "settings": json.dumps(settings),
            },
        )
        resp.raise_for_status()

