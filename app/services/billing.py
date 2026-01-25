from datetime import datetime, timedelta
from app.models import User

# начисление денег
async def add_balance(session, user: User, amount: int):
    user.balance += amount
    await session.commit()
    await session.refresh(user)

# списание денег
async def deduct_balance(session, user: User, amount: int) -> bool:
    if user.balance < amount:
        return False
    user.balance -= amount
    await session.commit()
    await session.refresh(user)
    return True

# продление подписки
async def extend_subscription(session, user: User, days: int):
    now = datetime.utcnow()
    if user.expire_at and user.expire_at > now:
        user.expire_at += timedelta(days=days)
    else:
        user.expire_at = now + timedelta(days=days)

    await session.commit()
    await session.refresh(user)

