from sqlalchemy import select
from app.models import User

async def get_or_create_user(session, telegram_id: str, referrer_id: int | None = None):
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()

    if user:
        return user, False

    user = User(
        telegram_id=telegram_id,
        referrer_id=referrer_id,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user, True

