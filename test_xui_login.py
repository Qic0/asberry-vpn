import asyncio
import httpx
from app.config import settings


async def main():
    url = f"{settings.XUI_PANEL_URL.rstrip('/')}/login"

    async with httpx.AsyncClient(verify=False, timeout=15) as client:
        r = await client.post(
            url,
            data={
                "username": settings.XUI_USERNAME,
                "password": settings.XUI_PASSWORD,
            },
        )

        print("STATUS:", r.status_code)
        print("HEADERS:", r.headers)
        print("BODY:", r.text[:200])


asyncio.run(main())

