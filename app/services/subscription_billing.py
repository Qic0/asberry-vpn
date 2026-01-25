import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import User
from app.services.vpn_service import XUIClient

PRICE_PER_DAY = 5  # ₽


async def run_billing():
    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as session:
        # 🔒 DB-lock: блокируем всех активных пользователей
        result = await session.execute(
            select(User)
            .where(User.subscription_active == True)
            .with_for_update()
        )

        users = result.scalars().all()

        for user in users:
            # ❌ нет клиента — просто деактивируем
            if not user.xui_client_id:
                user.subscription_active = False
                continue

            # ✅ хватает денег — списываем
            if user.balance >= PRICE_PER_DAY:
                user.balance -= PRICE_PER_DAY

                # продлеваем подписку (информационно)
                if user.subscription_until and user.subscription_until > now:
                    user.subscription_until += timedelta(days=1)
                else:
                    user.subscription_until = now + timedelta(days=1)

            # ❌ денег не хватает — отключаем VPN
            else:
                xui = XUIClient()
                try:
                    await xui.disable_client(user.xui_client_id)
                finally:
                    await xui.close()

                user.subscription_active = False

        await session.commit()


def main():
    asyncio.run(run_billing())


if __name__ == "__main__":
    main()

