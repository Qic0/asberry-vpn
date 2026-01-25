import asyncio
import json
from uuid import uuid4

import httpx
from app.config import settings


class XUISafeClient:
    def __init__(self):
        self.base = settings.XUI_PANEL_URL.rstrip("/")
        self.username = settings.XUI_USERNAME
        self.password = settings.XUI_PASSWORD
        self.inbound_id = settings.XUI_INBOUND_ID
        self.client = httpx.AsyncClient(verify=False, timeout=20)

    async def login(self):
        r = await self.client.post(
            f"{self.base}/login",
            data={
                "username": self.username,
                "password": self.password,
            },
        )
        r.raise_for_status()
        print("✅ LOGIN OK (cookie received)")

    async def get_inbound(self):
        r = await self.client.get(
            f"{self.base}/panel/api/inbounds/get/{self.inbound_id}"
        )
        r.raise_for_status()
        return r.json()["obj"]

    async def update_inbound(self, inbound: dict):
        r = await self.client.post(
            f"{self.base}/panel/api/inbounds/update/{self.inbound_id}",
            json=inbound,
        )
        r.raise_for_status()
        print("✅ INBOUND UPDATED")

    async def close(self):
        await self.client.aclose()


async def main():
    xui = XUISafeClient()
    await xui.login()

    inbound = await xui.get_inbound()

    settings_json = json.loads(inbound["settings"])
    clients = settings_json.get("clients", [])

    client_id = str(uuid4())
    email = f"tg_{client_id[:8]}"

    new_client = {
        "id": client_id,
        "email": email,
        "enable": True,
        "flow": "",
        "limitIp": 0,
        "totalGB": 0,
        "expiryTime": 0,
    }

    clients.append(new_client)
    settings_json["clients"] = clients

    inbound["settings"] = json.dumps(settings_json, ensure_ascii=False)

    await xui.update_inbound(inbound)

    sub_url = f"{settings.XUI_SUB_URL}/sub/{client_id}"

    print("\n🎉 CLIENT CREATED")
    print("CLIENT ID:", client_id)
    print("EMAIL:", email)
    print("SUB URL:")
    print(sub_url)

    await xui.close()


if __name__ == "__main__":
    asyncio.run(main())

