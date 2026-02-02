from datetime import datetime, timedelta
from app.models import User

DAILY_PRICE = 5  # рублей

async def try_extend_subscription(session, user: User) -> bool:
    if user.balance < DAILY_PRICE:
        user.subscription_active = False
        await session.commit()
        return False

    user.balance -= DAILY_PRICE
    now = datetime.utcnow()

    if user.subscription_until and user.subscription_until > now:
        user.subscription_until += timedelta(days=1)
    else:
        user.subscription_until = now + timedelta(days=1)

    user.subscription_active = True
    await session.commit()
    return True

