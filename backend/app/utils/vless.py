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
        f"&security=reality"
        f"&pbk={public_key}"
        f"&sid={short_id}"
        f"&sni={sni}"
        f"&fp=chrome"
        f"#${label}"
    )

