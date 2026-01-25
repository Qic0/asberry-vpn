import json
from uuid import uuid4
from urllib.parse import quote

import httpx
from app.config import settings


class XUIClient:
    def __init__(self):
        self.base = settings.XUI_PANEL_URL.rstrip("/")
        self.username = settings.XUI_USERNAME
        self.password = settings.XUI_PASSWORD
        self.inbound_id = int(settings.XUI_INBOUND_ID)

        self.client = httpx.AsyncClient(
            verify=False,
            timeout=20,
        )

    # ---------- AUTH ----------
    async def login(self):
        r = await self.client.post(
            f"{self.base}/login",
            data={
                "username": self.username,
                "password": self.password,
            },
        )
        r.raise_for_status()

        data = r.json()
        if not data.get("success"):
            raise RuntimeError("X-UI login failed")

    async def close(self):
        await self.client.aclose()

    # ---------- INBOUND ----------
    async def get_inbound(self) -> dict:
        r = await self.client.get(
            f"{self.base}/panel/api/inbounds/get/{self.inbound_id}"
        )
        r.raise_for_status()

        data = r.json()
        if not data.get("success"):
            raise RuntimeError("Failed to fetch inbound")

        return data["obj"]

    async def update_inbound(self, inbound: dict):
        r = await self.client.post(
            f"{self.base}/panel/api/inbounds/update/{self.inbound_id}",
            json=inbound,
        )
        r.raise_for_status()

        if not r.json().get("success"):
            raise RuntimeError("Failed to update inbound")

    # ---------- UNIQUE EMAIL ----------
    def _generate_unique_email(self, clients: list, base_email: str) -> str:
        """
        Генерирует уникальное имя клиента:
        tg_123
        tg_123/1
        tg_123/2
        ...
        """
        existing_emails = {c.get("email") for c in clients if c.get("email")}

        if base_email not in existing_emails:
            return base_email

        index = 1
        while True:
            candidate = f"{base_email}/{index}"
            if candidate not in existing_emails:
                return candidate
            index += 1

    # ---------- CLIENT CREATE ----------
    async def create_client(self, telegram_id: str) -> tuple[str, str]:
        await self.login()

        inbound = await self.get_inbound()

        settings_json = json.loads(inbound["settings"])
        clients = settings_json.get("clients", [])

        # базовое имя
        base_email = f"tg_{telegram_id}"

        # уникальное имя
        email = self._generate_unique_email(clients, base_email)

        client_id = str(uuid4())

        clients.append({
            "id": client_id,
            "email": email,
            "enable": True,
            "flow": "",
            "limitIp": 0,
            "totalGB": 0,
            "expiryTime": 0,
        })

        settings_json["clients"] = clients
        inbound["settings"] = json.dumps(settings_json, ensure_ascii=False)

        await self.update_inbound(inbound)

        return client_id, self._build_vless_url(
            client_id=client_id,
            email=email,
            inbound=inbound,
        )

    # ---------- CLIENT ENABLE / DISABLE ----------
    async def enable_client(self, client_id: str):
        await self._set_client_enabled(client_id, True)

    async def disable_client(self, client_id: str):
        await self._set_client_enabled(client_id, False)

    async def _set_client_enabled(self, client_id: str, enabled: bool):
        await self.login()

        inbound = await self.get_inbound()
        settings_json = json.loads(inbound["settings"])
        clients = settings_json.get("clients", [])

        for client in clients:
            if client.get("id") == client_id:
                client["enable"] = enabled
                inbound["settings"] = json.dumps(settings_json, ensure_ascii=False)
                await self.update_inbound(inbound)
                return

        raise RuntimeError("Client not found")

    # ---------- VLESS URL ----------
    def _build_vless_url(self, *, client_id: str, email: str, inbound: dict) -> str:
        stream = json.loads(inbound["streamSettings"])
        reality = stream.get("realitySettings", {})

        network = stream.get("network", "tcp")
        security = stream.get("security", "reality")

        pbk = settings.XUI_REALITY_PUBLIC_KEY
        sid = reality.get("shortIds", [""])[0]
        sni = reality.get("serverNames", [""])[0]
        spx = reality.get("spiderX", "/")

        host = settings.XUI_HOST
        port = inbound["port"]

        remark = f"Asberry-vpn-{email}"

        return (
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

