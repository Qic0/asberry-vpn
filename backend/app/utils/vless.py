from urllib.parse import quote


def generate_vless_reality(
    uuid: str,
    host: str,
    port: int,
    public_key: str,
    short_id: str,
    sni: str,
    label: str,
):
    return (
        f"vless://{uuid}@{host}:{port}"
        f"?type=tcp"
        f"&encryption=none"
        f"&flow=xtls-rprx-vision"
        f"&security=reality"
        f"&pbk={quote(str(public_key))}"
        f"&sid={quote(str(short_id))}"
        f"&sni={quote(str(sni))}"
        f"&fp=chrome"
        f"#{quote(str(label))}"
    )

