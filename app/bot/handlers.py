from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart

from app.database import AsyncSessionLocal
from app.services.users import get_or_create_user
from aiogram.types import WebAppInfo

router = Router()

@router.message(CommandStart())
async def start_handler(message: Message):
    async with AsyncSessionLocal() as session:
        await get_or_create_user(
            session=session,
            telegram_id=str(message.from_user.id),
        )

    await message.answer(
        "Добро пожаловать!\n\nОткройте приложение 👇",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[
                KeyboardButton(
                    text="📱 Перейти в приложение",
                    web_app=WebAppInfo(url="https://dycani.ru")
                )
            ]],
            resize_keyboard=True,
        ),
    )


# ================= TEST: ADD MONEY =================
@router.message(lambda m: m.text and m.text.startswith("/add_money"))
async def add_money_handler(message: Message):
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Используй: /add_money 50")
        return

    amount = int(parts[1])
    telegram_id = str(message.from_user.id)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await message.answer("❌ Пользователь не найден")
            return

        user.balance += amount
        await session.commit()

    await message.answer(
        f"✅ Баланс пополнен на {amount} ₽\n"
        f"💳 Текущий баланс: {user.balance} ₽"
    )

# ================= TEST: TAKE MONEY =================
@router.message(lambda m: m.text and m.text.startswith("/take_money"))
async def take_money_handler(message: Message):
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Используй: /take_money 5")
        return

    amount = int(parts[1])
    telegram_id = str(message.from_user.id)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await message.answer("❌ Пользователь не найден")
            return

        user.balance = max(0, user.balance - amount)
        await session.commit()

    await message.answer(
        f"❌ Списано {amount} ₽\n"
        f"💳 Баланс: {user.balance} ₽"
    )

