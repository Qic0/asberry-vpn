import json
import uuid
from urllib.parse import quote, urlparse

import requests

from app.config import settings


class XUIService:
    """
    Минимальный клиент для 3x-ui / X-UI (cookie-based auth).
    """

    def __init__(self):
        self.base_url = settings.XUI_BASE_URL.rstrip("/")
        self.panel_path = settings.XUI_PANEL_PATH.strip("/")
        self.session = requests.Session()
        # часто панели на self-signed
        self.session.verify = False
        self._login()

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        r = self.session.request(method, self._prefixed(path), **kwargs)
        if r.status_code in (401, 403):
            # сессия могла протухнуть — пробуем перелогиниться один раз
            self._login()
            r = self.session.request(method, self._prefixed(path), **kwargs)
        return r

    def _prefixed(self, path: str) -> str:
        if self.panel_path:
            return f"{self.base_url}/{self.panel_path}{path}"
        return f"{self.base_url}{path}"

    def _login(self) -> None:
        # большинство установок ожидают form-data
        r = self.session.post(
            self._prefixed("/login"),
            data={"username": settings.XUI_USERNAME, "password": settings.XUI_PASSWORD},
        )
        r.raise_for_status()

    def get_inbound(self, inbound_id: int) -> dict:
        r = self._request("GET", f"/panel/api/inbounds/get/{inbound_id}")
        r.raise_for_status()
        data = r.json()
        if not data.get("success"):
            raise RuntimeError(f"Failed to fetch inbound: {data.get('msg') or data}")
        return data["obj"]

    def _loads_json(self, value, default):
        if value is None:
            return default
        if isinstance(value, (dict, list)):
            return value
        if isinstance(value, str) and value.strip():
            return json.loads(value)
        return default

    def _derive_public_key(self, private_key: str) -> str | None:
        if not private_key:
            return None
        try:
            from cryptography.hazmat.primitives.asymmetric import x25519
            from cryptography.hazmat.primitives import serialization
        except Exception:
            return None

        import base64

        def _b64decode_nopad(s: str) -> bytes:
            s = s.strip()
            pad = "=" * (-len(s) % 4)
            try:
                return base64.urlsafe_b64decode(s + pad)
            except Exception:
                return base64.b64decode(s + pad)

        try:
            raw = _b64decode_nopad(private_key)
            if len(raw) != 32:
                return None
            pk = x25519.X25519PrivateKey.from_private_bytes(raw)
            pub = pk.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
            return base64.b64encode(pub).decode().rstrip("=")
        except Exception:
            return None

    def update_inbound_settings(self, inbound_id: int, settings_json: dict) -> None:
        inbound = self.get_inbound(inbound_id)

        payload = {
            "id": inbound_id,
            "remark": inbound.get("remark") or "",
            "enable": inbound.get("enable", True),
            "port": inbound.get("port"),
            "protocol": inbound.get("protocol"),
            "settings": json.dumps(settings_json, ensure_ascii=False),
            "streamSettings": inbound.get("streamSettings") or "{}",
            "sniffing": inbound.get("sniffing") or "{}",
            "allocate": inbound.get("allocate") or "{}",
            "tag": inbound.get("tag") or "",
            "listen": inbound.get("listen") or "",
            "total": inbound.get("total", 0),
            "expiryTime": inbound.get("expiryTime", 0),
        }

        # разные версии 3x-ui / x-ui используют разные пути update
        paths = [
            "/panel/api/inbounds/update",
            f"/panel/api/inbounds/update/{inbound_id}",
            "/api/inbounds/update",
            f"/api/inbounds/update/{inbound_id}",
        ]

        last_404 = None
        for path in paths:
            r = self._request("POST", path, json=payload)
            if r.status_code == 404:
                last_404 = r
                continue
            r.raise_for_status()
            data = r.json()
            if not data.get("success"):
                raise RuntimeError(f"Failed to update inbound settings: {data.get('msg') or data}")
            return

        # если все варианты не найдены
        detail = ""
        if last_404 is not None:
            detail = f" (last response: {last_404.status_code} {last_404.text[:200]})"
        raise RuntimeError(
            "X-UI update endpoint not found. Tried: "
            + ", ".join(paths)
            + detail
        )

    def _generate_unique_email(self, base: str, clients: list[dict]) -> str:
        existing = {c.get("email") for c in clients if isinstance(c, dict)}
        if base not in existing:
            return base
        i = 1
        while f"{base}/{i}" in existing:
            i += 1
        return f"{base}/{i}"

    def create_client(
        self,
        *,
        inbound_id: int,
        telegram_id: int,
        device_number: int,
        name: str | None = None,
    ) -> tuple[str, str, str, str]:
        inbound = self.get_inbound(inbound_id)
        inbound_settings = self._loads_json(inbound.get("settings"), {})  # dict
        clients = inbound_settings.get("clients", [])

        email_base = f"tg_{telegram_id}"
        email = self._generate_unique_email(email_base, clients)

        client_uuid = str(uuid.uuid4())
        sub_id = uuid.uuid4().hex[:16]

        clients.append(
            {
                "id": client_uuid,
                "email": email,
                "enable": True,
                "flow": "xtls-rprx-vision",
                "limitIp": 0,
                "totalGB": 0,
                "expiryTime": 0,
                "tgId": telegram_id,
                "subId": sub_id,
                "comment": name or f"device-{device_number}",
                "reset": 0,
            }
        )

        inbound_settings["clients"] = clients
        self.update_inbound_settings(inbound_id, inbound_settings)

        vless_url = self.build_vless_url(
            client_uuid=client_uuid,
            email=email,
            inbound=inbound,
            name=name,
        )

        return client_uuid, sub_id, vless_url, email

    def get_clients_map(self, inbound_id: int) -> dict[str, str]:
        inbound = self.get_inbound(inbound_id)
        inbound_settings = self._loads_json(inbound.get("settings"), {})
        clients = inbound_settings.get("clients", [])
        result: dict[str, str] = {}
        for c in clients:
            if not isinstance(c, dict):
                continue
            cid = c.get("id")
            email = c.get("email")
            if cid and email:
                result[str(cid)] = str(email)
        return result

    def set_client_enabled(self, *, inbound_id: int, client_uuid: str, enabled: bool) -> None:
        inbound = self.get_inbound(inbound_id)
        inbound_settings = self._loads_json(inbound.get("settings"), {})
        clients = inbound_settings.get("clients", [])

        for c in clients:
            if c.get("id") == client_uuid:
                c["enable"] = enabled
                break
        else:
            raise RuntimeError("Client not found in inbound settings")

        inbound_settings["clients"] = clients
        self.update_inbound_settings(inbound_id, inbound_settings)

    def delete_client(self, *, inbound_id: int, client_uuid: str) -> None:
        inbound = self.get_inbound(inbound_id)
        inbound_settings = self._loads_json(inbound.get("settings"), {})
        clients = inbound_settings.get("clients", [])

        new_clients = [c for c in clients if c.get("id") != client_uuid]
        if len(new_clients) == len(clients):
            raise RuntimeError("Client not found in inbound settings")

        inbound_settings["clients"] = new_clients
        self.update_inbound_settings(inbound_id, inbound_settings)

    def _build_remark(self, *, email: str, name: str | None) -> str:
        prefix = (settings.VLESS_REMARK_PREFIX or "Asberry").strip()
        display = (name or email or "device").strip()
        remark = f"{prefix} - {display}".strip()
        flag = (settings.VLESS_REMARK_FLAG or "").strip()
        if flag:
            remark = f"{flag} {remark}".strip()
        return remark

    def build_vless_url(self, *, client_uuid: str, email: str, inbound: dict, name: str | None = None) -> str:
        """
        Собирает VLESS Reality ссылку на основе inbound streamSettings.
        """
        stream = self._loads_json(inbound.get("streamSettings"), {})
        reality = stream.get("realitySettings", {}) or {}

        host = settings.XUI_HOST or (urlparse(self.base_url).hostname or "")
        port = inbound["port"]

        pbk = settings.XUI_REALITY_PUBLIC_KEY or reality.get("publicKey") or reality.get("public_key") or ""
        if not pbk:
            derived = self._derive_public_key(reality.get("privateKey", ""))
            if derived:
                pbk = derived
        sni = (reality.get("serverNames") or [""])[0]
        sid = (reality.get("shortIds") or [""])[0]
        spx = reality.get("spiderX", "/")

        remark = self._build_remark(email=email, name=name)

        return (
            f"vless://{client_uuid}@{host}:{port}"
            f"?type=tcp"
            f"&encryption=none"
            f"&flow=xtls-rprx-vision"
            f"&security=reality"
            f"&pbk={quote(str(pbk), safe='')}"
            f"&fp=chrome"
            f"&sni={quote(str(sni), safe='')}"
            f"&sid={quote(str(sid), safe='')}"
            f"&spx={quote(str(spx), safe='')}"
            f"#{quote(remark, safe='')}"
        )
