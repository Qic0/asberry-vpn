from app.models import User

REFERRAL_BONUS = 50  # рублей

async def reward_referrer(session, referrer: User):
    referrer.balance += REFERRAL_BONUS
    await session.commit()

