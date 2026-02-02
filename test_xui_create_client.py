import asyncio
import json
from uuid import uuid4
from urllib.parse import quote

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


def build_vless_url(
    *,
    client_id: str,
    email: str,
    inbound: dict,
) -> str:
    """
    Формирует VLESS URL на основе реальных настроек inbound (как X-UI)
    """

    stream = json.loads(inbound["streamSettings"])
    reality = stream.get("realitySettings", {})

    network = stream.get("network", "tcp")
    security = stream.get("security", "reality")

    pbk = reality.get("publicKey")
    sid = reality.get("shortIds", [""])[0]
    sni = reality.get("serverNames", [""])[0]
    spx = reality.get("spiderX", "/")

    host = settings.XUI_HOST  # IP или домен сервера
    port = inbound["port"]

    remark = f"Asberry-vpn-{email}"

    url = (
        f"vless://{client_id}@{host}:{port}"
        f"?type={network}"
        f"&encryption=none"
        f"&security={security}"
        f"&pbk={pbk}"
        f"&fp=chrome"
        f"&sni={sni}"
        f"&sid={sid}"
        f"&spx={quote(spx)}"
        f"#{quote(remark)}"
    )

    return url


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

    vless_url = build_vless_url(
        client_id=client_id,
        email=email,
        inbound=inbound,
    )

    print("\n🎉 CLIENT CREATED")
    print("CLIENT ID:", client_id)
    print("EMAIL:", email)
    print("\n🔗 VLESS URL (READY TO USE):\n")
    print(vless_url)

    await xui.close()


if __name__ == "__main__":
    asyncio.run(main())

